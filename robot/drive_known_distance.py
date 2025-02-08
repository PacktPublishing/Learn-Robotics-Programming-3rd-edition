import json
import time
import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController


class DriveKnownDistanceBehavior:
    def __init__(self):
        self.speed = 0.6
        self.expected_distance = 1000
        self.distance_pid = PIDController(0.02, 0.001)
        self.balance_pid = PIDController(0.01, 0.003)
        self.last_update = time.time()
        self.distance_reached = False

    def calculate_speed(self, left_encoder, right_encoder, time_difference):
        left_gap = self.expected_distance - left_encoder
        right_gap = self.expected_distance - right_encoder
        if abs(left_gap) > abs(right_gap):
            distance_error = left_gap
        else:
            distance_error = right_gap

        if abs(distance_error) < 1:
            self.distance_reached = True
            speed = 0
        else:
            speed = np.clip(
                self.distance_pid.control(distance_error, time_difference),
                -self.speed,
                self.speed)
        return speed

    def calculate_balance(self, left_encoder, right_encoder, time_difference):
        error = left_encoder - right_encoder
        return self.balance_pid.control(error, time_difference)

    def on_encoders_data(self, client, userdata, message):
        encoder_data = json.loads(message.payload)
        left_encoder = encoder_data['left_distance']
        right_encoder = encoder_data['right_distance']

        new_time = time.time()
        time_difference = new_time - self.last_update
        self.last_update = new_time

        speed = self.calculate_speed(left_encoder, right_encoder, time_difference)
        balance = self.calculate_balance(left_encoder, right_encoder, time_difference)
        print(left_encoder, right_encoder,
              time_difference, speed, balance, self.distance_pid.integral)
        left_speed = speed - balance
        right_speed = speed + balance
        publish_json(client, "motors/wheels", [left_speed, right_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        while not self.distance_reached:
            client.loop()


behavior = DriveKnownDistanceBehavior()
behavior.start()
