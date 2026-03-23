import time
import numpy as np
import ujson as json

from common.mqtt_behavior import connect, publish_json


class SmoothDistanceAvoiderBehavior:
    def __init__(self):
        self.speed = 0.6
        self.curve_proportion = 40

    def on_distance_message(self, client, userdata, message):
        # Sense
        sensor_data = np.array(json.loads(message.payload))
        grid = np.fliplr(sensor_data.reshape((8, 8)))
        top_lines = grid[4:, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        left_distance = int(np.min(left_sensors))
        right_distance = int(np.min(right_sensors))
        publish_json(client, "smooth_distance_avoider/plot", {
            "left_distance": left_distance,
            "right_distance": right_distance,
            "time": time.time()
        })

        # Think
        nearest_distance = min(left_distance, right_distance)
        inverse = 1/max(nearest_distance, 1)
        self.curve = self.curve_proportion * inverse

        furthest_speed = np.clip(self.speed - self.curve, -1, 1)
        nearest_speed = np.clip(self.speed + self.curve, -1, 1)

        if left_distance < right_distance:
            left_motor_speed = nearest_speed
            right_motor_speed = furthest_speed
        else:
            left_motor_speed = furthest_speed
            right_motor_speed = nearest_speed

        # Act
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.on_distance_message)
        client.publish("sensors/distance/control/start_ranging", "")
        client.loop_forever()


behavior = SmoothDistanceAvoiderBehavior()
behavior.start()
