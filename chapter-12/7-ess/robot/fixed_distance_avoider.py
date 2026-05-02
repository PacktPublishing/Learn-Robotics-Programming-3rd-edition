import time
import numpy as np
import ujson as json

from common.mqtt_behavior import connect, publish_json


class FixedDistanceAvoiderBehavior:
    def __init__(self):
        self.speed = 0.8
        self.threshold = 300

    def on_distance_message(self, client, userdata, message):
        # Sense
        sensor_data = np.array(json.loads(message.payload))
        grid = np.fliplr(sensor_data.reshape((8, 8)))
        top_lines = grid[4:, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        left_distance = int(np.min(left_sensors))
        right_distance = int(np.min(right_sensors))
        publish_json(client, "fixed_distance_avoider/plot", {
            "left_distance": left_distance,
            "right_distance": right_distance,
            "time": time.time()
        })

        # Think
        left_motor_speed = self.speed
        right_motor_speed = self.speed
        if left_distance < self.threshold:
            right_motor_speed = -self.speed
        elif right_distance < self.threshold:
            left_motor_speed = -self.speed

        # Act
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.on_distance_message)
        client.publish("sensors/distance/control/start_ranging", "")
        client.loop_forever()


behavior = FixedDistanceAvoiderBehavior()
behavior.start()
