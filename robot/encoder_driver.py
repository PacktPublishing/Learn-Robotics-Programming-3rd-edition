"""
The encoder driver will drive the robot using the encoders.
Responsibilities:
- Driving in a straight line, keeping motors at the same speed.
- Driving for a fixed distance.
- Driving for a fixed time.
- Stopped by an e-stop.

All modes will correct the speed of the motors to keep the robot driving straight using
an encoder/PID loop.

This accepts MQTT messages:
- drive/start: {"distance_mm": 100, "speed": 0.8} -> Will drive and stop at the given distance.
- drive/start: {"time_s": 3, "speed": 0.8} -> Will drive for the given time.
- drive/start: {"speed": 0.8} -> Will drive until stopped.
- drive/settings: {"diff_proportion": 0.2, "veer_integral": 0.3} -> Update the PID settings.
- drive/stop: {}
- stop/all: {}

This will run as a service.
It will also offer a port 5002 for a bokeh server to display the encoder data and PID errors.


Sequence for driving forever:
launcher/start "encoder driver" 
    -> drive/start: {"speed": 0.8} -> drive/stop: {}
    -> drive/start: {"speed": 0.6} -> drive/stop: {}
launcher/stop "encoder driver"

Sequence for driving for a fixed distance:
launcher/start "encoder driver" 
    -> drive/start: {"distance_mm": 100, "speed": 0.8}
    -> drive/start: {"distance_mm": 80, "speed": 0.8}
launcher/stop "encoder driver"

Sequence for driving for a fixed time:
launcher/start "encoder driver" 
    -> drive/start: {"time_s": 3, "speed": 0.8}
    -> drive/start: {"time_s": 2, "speed": 0.8}
launcher/stop "encoder driver"

"""
import numpy as np
import ujson as json

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.handler import Handler
from bokeh.plotting import figure, ColumnDataSource
from bokeh.document import Document

from common.mqtt_behavior import connect, publish_json
from common.pid_control import PIController


class DataLogger(Handler):
    """Graph and log data"""
    def __init__(self):
        super().__init__()
        self.mqtt_client = None
        self.diff_data = np.zeros(100)
        self.error_data = np.zeros(100)
        self.timestamps = np.linspace(0, 10, 100)
    
    def log(self, data):
        if self.mqtt_client:
            publish_json(self.mqtt_client, "behavior/log", data)
        self.error_data = np.roll(self.error_data, 1)
        self.error_data[0] = data["error"]
        self.diff_data = np.roll(self.diff_data, 1)
        self.diff_data[0] = data["diff"]

    def modify_document(self, doc: Document) -> None:
        column_source = ColumnDataSource({'error': [], 'diff': [], 'timestamps': []})
        def update():
            column_source.data = {
                'error': np.flip(self.error_data),
                'diff': np.flip(self.diff_data),
                'timestamps': self.timestamps}
        doc.add_periodic_callback(update, 50)
        fig = figure(title="Encoder data", x_axis_label="time", y_axis_label="mm")
        fig.line('timestamps', 'error', source=column_source, line_width=2, line_color='red')
        fig.line('timestamps', 'diff', source=column_source, line_width=2, line_color='blue')
        doc.add_root(fig)


class StopMode:
    def think(self, sensor_data):
        return 0, 0
    def apply_settings(self, settings):
        pass


class DriveForeverMode:
    # Given settings, will transform encoder data into motor speeds.
    def __init__(self, speed, logger: DataLogger):
        self.speed = speed
        # Lower proportion = smoother, but more likely to steer into something.
        # Higher proportion, corrects away from a collision, but will have a characteristic proportional wobble.

        # A differential PID
        self.diff_pid = PIController(0.2, 0.3)
        # Motor PIDs
        self.left_pid = PIController(0.2, 0.3)
        self.right_pid = PIController(0.2, 0.3)
        self.logger = logger

    def apply_settings(self, settings):
        if "diff_proportion" in settings:
            self.diff_pid.k_p = settings["diff_proportion"]
        if "diff_integral" in settings:
            self.diff_pid.k_i = settings["diff_integral"]
        if "speed" in settings:
            self.speed = settings["speed"]
        if "motor_proportion" in settings:
            self.left_pid.k_p = settings["motor_proportion"]
            self.right_pid.k_p = settings["motor_proportion"]
        if "motor_integral" in settings:
            self.left_pid.k_i = settings["motor_integral"]
            self.right_pid.k_i = settings["motor_integral"]

    def think(self, sensor_data):
        # Think
        left = sensor_data["left_delta"]
        right = sensor_data["right_delta"]
        delta_time = sensor_data["delta_time"]
        # Apply differential PID
        error = right - left
        diff = self.diff_pid.control(error, delta_time)
        left_motor_input = self.speed + diff
        right_motor_input = self.speed - diff
        # Apply motor PIDS
        left_motor_error = left_motor_input - left
        right_motor_error = right_motor_input - right
        left_motor_speed = self.left_pid.control(left_motor_error, delta_time)
        right_motor_speed = self.right_pid.control(right_motor_error, delta_time)
        left_motor_speed = np.clip(left_motor_speed, -1, 1)
        right_motor_speed = np.clip(right_motor_speed, -1, 1)
        
        self.logger.log({
            "left": left,
            "right": right,
            "diff": diff,
            "error": error,
            "left_motor_input": left_motor_input,
            "right_motor_input": right_motor_input,
            "left_motor_speed": left_motor_speed,
            "right_motor_speed": right_motor_speed,
        })
        return left_motor_speed, right_motor_speed


class DriveForTimeMode(DriveForeverMode):
    time_s = None
    start_time = None
    # TODO: How could it share the same PID? Should it?
    def start(self, time_s):
        self.time_s = time_s

    def think(self, sensor_data):
        if self.start_time is None:
            self.start_time = sensor_data["time"]
        if sensor_data["time"] - self.start_time > self.time_s:
            return 0, 0
        return super().think(sensor_data)


class DrivingBehavior:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.stop_mode = StopMode()
        self.drive_forever_mode = DriveForeverMode(0.6, self.logger)
        self.current_mode = self.stop_mode
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data", self.data_received)
        client.subscribe("drive/#")
        client.message_callback_add("drive/settings", self.apply_settings)
        client.message_callback_add("drive/start", self.start_drive)
        client.message_callback_add("drive/stop", self.stop_drive)
        client.subscribe("all/stop")
        client.message_callback_add("all/stop", self.stop_drive)
        publish_json(
            client, "sensors/encoders/control", 
            {"running": True, "frequency": 10, "reset": True}
        )
        # Finish drive mode setup
        self.logger.mqtt_client = client
    
    def apply_settings(self, client, userdata, msg):
        settings = json.loads(msg.payload)
        self.drive_forever_mode.apply_settings(settings)
    
    def start_drive(self, client, userdata, msg):
        # settings = json.loads(msg.payload)
        # if "distance_mm" in settings:
        #     self.current_mode = StopAction()
        # elif "time_s" in settings:
        #     self.current_mode = StopAction()
        # else:
        self.current_mode = self.drive_forever_mode

    def stop_drive(self, client, userdata, msg):
        self.current_mode = self.stop_mode

    def data_received(self, client, userdata, msg):
        # Sense
        sensor_data = json.loads(msg.payload)
        # Think
        left_motor_speed, right_motor_speed = self.current_mode.think(sensor_data)
        # Act
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def run(self):
        self.client = connect(self.on_connect, start_loop=False)
        self.client.loop_start()


logger = DataLogger()
behavior = DrivingBehavior(logger)
behavior.run()
apps = {'/': Application(logger)}

server = Server(apps, port=5002, address="0.0.0.0", allow_websocket_origin=["*"])
server.start()
server.run_until_shutdown()
