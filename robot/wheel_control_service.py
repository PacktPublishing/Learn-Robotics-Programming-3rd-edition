import ujson as json
import time
import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController
from common.time_stepper import TimeStepper


class WheelControlService:
    def __init__(self):
        self.max_mm_per_second = 200
        self.left_speed = 0
        self.right_speed = 0
        self.left_pid = PIDController(0.004, 0.008)
        self.right_pid = PIDController(0.004, 0.008)
        self.time_stepper = TimeStepper()
        self.enabled = False

    def on_encoders_data(self, client, userdata, message):
        if not self.enabled:
            return
        encoder_data = json.loads(message.payload)
        left_encoder = encoder_data['left_mm_per_sec']
        right_encoder = encoder_data['right_mm_per_sec']
        time_difference = self.time_stepper.step()

        # Get the error
        left_error = self.left_speed - left_encoder
        right_error = self.right_speed - right_encoder
        left_control = self.left_pid.control(left_error, time_difference)
        right_control = self.right_pid.control(right_error, time_difference)
        publish_json(client, "wheel_control/plot", {
            "left_error": left_error, "left_control": left_control,
            "right_error": right_error, "right_control": right_control,
            "time": time.time()})

        publish_json(client, "motors/wheels", [left_control, right_control])

    def on_enabled(self, client, userdata, message):
        self.enabled = json.loads(message.payload)

    def on_wheel_speed_mm(self, client, userdata, message):
        data = json.loads(message.payload)
        self.left_speed = np.clip(data[0], -self.max_mm_per_second,
                                  self.max_mm_per_second)
        self.right_speed = np.clip(data[1], -self.max_mm_per_second,
                                   self.max_mm_per_second)

    def on_config_updated(self, client, userdata, message):
        data = json.loads(message.payload)
        if 'wheel_control/max_mm_per_second' in data:
            self.max_mm_per_second = data['wheel_control/max_mm_per_second']
        self.left_pid.handle_config_messages(data, 'wheel_control')
        self.right_pid.handle_config_messages(data, 'wheel_control')

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        client.subscribe("wheel_control/#")
        client.message_callback_add("wheel_control/enabled",
                                    self.on_enabled)
        client.message_callback_add("wheel_control/wheel_speed_mm",
                                    self.on_wheel_speed_mm)
        publish_json(client, "config/get",
                       ["wheel_control/max_mm_per_second",
                        "wheel_control/proportional",
                        "wheel_control/integral"])
        client.loop_forever()

service = WheelControlService()
service.start()
