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
low_probability = 10 ** -10

class Localisation:
    def __init__(self):
        self.poses = np.column_stack((
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 2 * np.pi, population_size)
        ))
        self.wheel_distance = 0

        self.alpha_trans_trans = 1.2/100
        self.alpha_trans_rot = 0.5/100
        self.alpha_rot_rot = 2/100
        self.alpha_rot_trans = 0.1/100

        self.config_ready = False
        self.previous_left_distance = 0
        self.previous_right_distance = 0

    def in_boundary(self):
        inside_walls = np.logical_and(
            np.logical_and(self.poses[:, 0] > 0, self.poses[:, 0] < 1500),
            np.logical_and(self.poses[:, 1] > 0, self.poses[:, 1] < 1500)
        )
        not_in_cutouts = np.logical_not(
            np.logical_and(self.poses[:, 0] < 1000, self.poses[:, 1] > 500)
        )
        return np.logical_and(inside_walls, not_in_cutouts)

    def observational_model(self):
        weights = np.ones(population_size, dtype=np.float32)
        weights = np.where(np.logical_not(self.in_boundary()), weights, low_probability)
        return weights

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

    def randomise_motion(self, translation, rotation):
        trans_scale = self.alpha_trans_trans * abs(translation) \
            + self.alpha_trans_rot * abs(rotation)
        rot_scale = self.alpha_rot_rot * abs(rotation) \
            + self.alpha_rot_trans * abs(translation)
        trans_samples = np.random.normal(translation, trans_scale, population_size)
        rot_samples = np.random.normal(rotation, rot_scale, population_size)
        return trans_samples, rot_samples

    def move_poses(self, rotation, translation):
        self.poses = rotated_poses(self.poses, rotation)
        self.poses = translated_poses(self.poses, translation)
        self.poses = rotated_poses(self.poses, rotation)

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        left_distance_delta = distance_data['left_distance'] - self.previous_left_distance
        right_distance_delta = distance_data['right_distance'] - self.previous_right_distance
        self.previous_left_distance = distance_data['left_distance']
        self.previous_right_distance = distance_data['right_distance']

        # Think
        translation, theta = self.convert_encoders_to_motion(left_distance_delta, right_distance_delta)
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(translation, rotation)
        self.move_poses(rot_samples, trans_samples)
        weights = self.observational_model()
        print(weights)
        # Act
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
