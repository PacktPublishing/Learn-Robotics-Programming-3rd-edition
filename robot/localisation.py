import ujson as json
import time

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import rotated_poses, translated_poses

walls = [
    (0, 1500),
    (1500, 1500),
    (1500, 500),
    (1000, 500),
    (1000, 0),
    (0, 0)
]
population_size = 200

class Localisation:
    def __init__(self):
        self.poses = np.column_stack((
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 2 * np.pi, population_size)
        ))
        self.wheel_distance = 0
        self.config_ready = False
        self.previous_left_distance = 0
        self.previous_right_distance = 0

    def keep_points_in_boundary(self):
        poses_in_bounds = np.logical_not(
            np.logical_and(
                np.greater(self.poses[:, 0], 1000),
                np.less(self.poses[:, 1], 500)
            )
        )
        self.poses = self.poses[poses_in_bounds]


    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def publish_poses(self, client):
        publish_json(client, "localisation/poses", self.poses.tolist())

    def publish_map(self, client):
        publish_json(client, "localisation/map", {
            "walls": walls
        })

    def convert_encoders_to_motion(self, left_distance_delta, right_distance_delta):
        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            return left_distance_delta, 0

        mid_distance = (left_distance_delta + right_distance_delta) / 2
        theta = (right_distance_delta - left_distance_delta) / self.wheel_distance

        return mid_distance, theta

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        left_distance_delta = distance_data['left_distance'] - self.previous_left_distance
        right_distance_delta = distance_data['right_distance'] - self.previous_right_distance
        self.previous_left_distance = distance_data['left_distance']
        self.previous_right_distance = distance_data['right_distance']

        # Think
        mid_distance, theta = self.convert_encoders_to_motion(left_distance_delta, right_distance_delta)
        # Act
        self.poses = rotated_poses(self.poses, theta / 2)
        self.poses = translated_poses(self.poses, mid_distance)
        self.poses = rotated_poses(self.poses, theta / 2)
        self.keep_points_in_boundary()

        self.publish_poses(client)

    def start(self):
        client = connect()
        self.publish_poses(client)
        self.publish_map(client)
        print("Waiting for config")
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "robot/wheel_distance",
                        ])
        while not self.config_ready:
            time.sleep(0.1)
        print("Config received. Now wiating for sensor data...")

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        while True:
            time.sleep(0.1)


service = Localisation()
service.start()
