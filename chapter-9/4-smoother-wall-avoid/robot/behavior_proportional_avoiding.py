from time import sleep
import common.mqtt_behavior as mqtt_behavior
import numpy as np
import ujson as json
from common.helpers import clamp

class ObstacleAvoidingBehavior:
    def __init__(self):
        self.speed = 0.6
        self.curve_proportion = 70

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)
        client.publish("sensors/distance/control/start_ranging", " ")

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
        nearest_distance = min(left_distance, right_distance)
        inverse = 1/max(nearest_distance, 1)
        curve = self.curve_proportion * inverse
        furthest_speed = clamp(self.speed - curve, -1, 1)
        nearest_speed = clamp(self.speed + curve, -1, 1)

        if left_distance < right_distance:
            left_motor_speed = nearest_speed
            right_motor_speed = furthest_speed
        else:
            left_motor_speed = furthest_speed
            right_motor_speed = nearest_speed

        # Act
        print(left_distance,right_distance,left_motor_speed,right_motor_speed)
        self.client.publish("log/obstacle_avoiding/proportional", json.dumps([left_distance,right_distance,left_motor_speed,right_motor_speed]))
        self.client.publish("motors/set_both", json.dumps([left_motor_speed, right_motor_speed]))

    def loop_forever(self):
        self.client = mqtt_behavior.connect(self.on_connect, start_loop=False)
        try:
            self.client.loop_forever()
        finally:
            self.client.publish(
                "sensors/distance/control/stop_ranging", " ", qos=1)\
                    .wait_for_publish()
            self.client.publish("motors/stop", " ", qos=1)\
                .wait_for_publish()
            self.client.disconnect()

behavior = ObstacleAvoidingBehavior()
behavior.loop_forever()
