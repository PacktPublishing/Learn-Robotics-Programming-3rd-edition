import ujson as json
import time

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController
from common.time_stepper import TimeStepper

class DriveKnownDistanceBehavior:
    def __init__(self):
        self.time_stepper = TimeStepper()
        self.distance_pid = PIDController(0.2, 0.01)
        self.expected_distance = 1000
        self.distance_reached = False

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        time_difference = self.time_stepper.step()
        left_error = self.expected_distance - distance_data['left_distance']
        right_error = self.expected_distance - distance_data['right_distance']

        publish_json(client, "drive_known_distance/plot", {
            "left_error": left_error,
            "right_error": right_error,
            "time": time.time()
        })
        # Think
        if abs(left_error) > abs(right_error):
            distance_error = left_error
        else:
            distance_error = right_error
        if abs(distance_error) < 1:
            self.distance_reached = True
            speed = 0
        else:
            speed = self.distance_pid.control(distance_error, time_difference)
        # Act
        publish_json(client, "wheel_control/wheel_speed_mm", [speed, speed])

    def on_config_updated(self, client, userdata, message):
        data = json.loads(message.payload)
        self.distance_pid.handle_config_messages(data, 'drive_known_distance')

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        while not self.distance_reached:
            client.loop()


behavior = DriveKnownDistanceBehavior()
behavior.start()
