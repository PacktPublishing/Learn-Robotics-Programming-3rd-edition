import ujson as json
import time

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class DriveKnownDistanceBehavior:
    def __init__(self):
        self.max_speed_mm = 200
        self.expected_distance = 1000
        self.distance_pid = PIDController(0.2, 0.01)
        self.left_pid = PIDController(0.004, 0.008)
        self.right_pid = PIDController(0.004, 0.008)
        self.last_update = time.time()
        self.distance_reached = False

    def calculate_speed(self, client, distance_data, time_difference):
        left_error = self.expected_distance - distance_data['left_distance']
        right_error = self.expected_distance - distance_data['right_distance']
        publish_json(client, "drive_known_distance/plot", {
            "left_error": left_error,
            "right_error": right_error,
            "time": time.time()
        })
        if abs(left_error) > abs(right_error):
            distance_error = left_error
        else:
            distance_error = right_error
        if abs(distance_error) < 1:
            self.distance_reached = True
            speed = 0
        else:
            speed = np.clip(
                self.distance_pid.control(distance_error, time_difference),
                -self.max_speed_mm,
                self.max_speed_mm)
        return speed

    def motor_speed_correction(self, speed, distance_data, time_difference):
        left_mm_error = speed - distance_data['left_mm_per_sec']
        right_mm_error = speed - distance_data['right_mm_per_sec']
        left_control = self.left_pid.control(left_mm_error, time_difference)
        right_control = self.right_pid.control(right_mm_error, time_difference)
        return left_control, right_control

    def time_step(self):
        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time
        return time_difference

    def on_encoders_data(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        time_difference = self.time_step()
        speed = self.calculate_speed(client, distance_data, time_difference)
        left_control, right_control = self.motor_speed_correction(
            speed, distance_data, time_difference)
        publish_json(client, "motors/wheels", [left_control, right_control])

    def on_config_updated(self, client, userdata, message):
        data = json.loads(message.payload)
        if 'drive_known_distance/max_mm_per_second' in data:
            self.mm_per_second = data['closed_loop_motor/max_mm_per_second']
        if 'drive_known_distance/proportional' in data:
            self.distance_pid.proportional_constant = data['drive_known_distance/proportional']
        if 'drive_known_distance/integral' in data:
            self.distance_pid.integral_constant = data['drive_known_distance/integral']
            self.distance_pid.integral = 0
        if 'closed_loop_motor/proportional' in data:
            self.left_pid.proportional_constant = data['closed_loop_motor/proportional']
            self.right_pid.proportional_constant = data['closed_loop_motor/proportional']
        if 'closed_loop_motor/integral' in data:
            self.left_pid.integral_constant = data['closed_loop_motor/integral']
            self.left_pid.integral = 0
            self.right_pid.integral_constant = data['closed_loop_motor/integral']
            self.right_pid.integral = 0

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
