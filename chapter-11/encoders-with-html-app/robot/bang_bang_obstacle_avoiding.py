from time import sleep
from common.mqtt_behavior import connect, publish_json
import numpy as np
import ujson as json


class BangBangObstacleAvoidingBehavior:
    def __init__(self):
        self.speed = 0.6

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)
        client.publish("sensors/distance/control", "start_ranging")

    def data_received(self, client, userdata, msg):
        # Sense
        sensor_data = json.loads(msg.payload)
        as_array = np.array(sensor_data)
        top_lines = as_array[:4, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        left_distance = int(np.min(left_sensors))
        right_distance = int(np.min(right_sensors))
        # Think
        left_motor_speed = self.speed
        right_motor_speed = self.speed
        if left_distance < 300:
            right_motor_speed = -self.speed
        elif right_distance < 300:
            left_motor_speed = -self.speed
        # Act
        log_data = {
            "left_distance": left_distance, 
            "right_distance": right_distance, 
            "left_motor_speed": left_motor_speed, 
            "right_motor_speed": right_motor_speed
        }
        publish_json(client, "log/obstacle_avoider", log_data)
        print(log_data)
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def run(self):
        self.client = connect(self.on_connect, start_loop=False)
        self.client.loop_forever()

behavior = BangBangObstacleAvoidingBehavior()
behavior.run()
