import json
import time

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import Pose, rotated_poses, translated_poses

width = 1500
height = 1500
cutout_left = 1000
cutout_top = 500
walls = [
    (0, height),
    (width, height),
    (width, cutout_top),
    (cutout_left, cutout_top),
    (cutout_left, 0),
    (0, 0)
]

population_size = 2000
rng = np.random.default_rng()
low_probability = 10 ** -10

class Localisation:
    def __init__(self):
        self.poses = np.empty((population_size,), dtype=Pose)
        self.poses['x'] = rng.uniform(0, width, population_size)
        self.poses['y'] = rng.uniform(0, height, population_size)
        self.poses['theta'] = rng.uniform(0, 2 * np.pi, population_size)

        self.wheel_distance = 0
        self.config_ready = False
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.alpha_trans_trans = 1.2/100
        self.alpha_trans_rot = 0.5/100
        self.alpha_rot_rot = 2/100
        self.alpha_rot_trans = 0.1/100

    def in_boundary(self):
        inside_walls = np.logical_and(
            np.logical_and(self.poses['x'] > 0, self.poses['x'] < width),
            np.logical_and(self.poses['y'] > 0, self.poses['y'] < height)
        )
        not_in_cutouts = np.logical_not(
            np.logical_and(self.poses['x'] > cutout_left, self.poses['y'] < cutout_top)
        )
        return np.logical_and(inside_walls, not_in_cutouts)

    def observational_model(self):
        weights = np.where(self.in_boundary(), 1.0, low_probability)
        return weights

    def resample_poses(self, weights, sample_count):
        normalised_weights = weights / np.sum(weights)
        return rng.choice(
            self.poses,
            size=sample_count,
            p=normalised_weights
        )

    def convert_encoders_to_motion(self, left_distance_delta, right_distance_delta):
        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            return left_distance_delta, 0

        mid_distance = (left_distance_delta + right_distance_delta) / 2
        theta = (right_distance_delta - left_distance_delta) / self.wheel_distance

        return mid_distance, theta

    def move_poses(self, rotation, translation):
        self.poses = rotated_poses(self.poses, rotation)
        self.poses = translated_poses(self.poses, translation)
        self.poses = rotated_poses(self.poses, rotation)

    def randomise_motion(self, translation, rotation):
        trans_scale = self.alpha_trans_trans * abs(translation) \
            + self.alpha_trans_rot * abs(rotation)
        rot_scale = self.alpha_rot_rot * abs(rotation) \
            + self.alpha_rot_trans * abs(translation)

        trans_samples = rng.normal(translation, trans_scale, population_size)
        rot_samples = rng.normal(rotation, rot_scale, population_size)

        return trans_samples, rot_samples

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
        self.poses = self.resample_poses(weights, population_size)
        # Act
        publish_sample = self.resample_poses(weights, 200)
        self.publish_poses(client, publish_sample)

    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        print(data)
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def publish_map(self, client):
        publish_json(client, "localisation/map", {
            "walls": walls
        })

    def start(self):
        client = connect()
        self.publish_map(client)
        print("Published map. Getting wheel distance config...")
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "robot/wheel_distance",
                        ])
        while not self.config_ready:
            time.sleep(0.1)
        print("Configuration received. Starting localisation.")

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        while True:
            time.sleep(0.1)

service = Localisation()
service.start()
