import json
import time

import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Poses
from observation_models.boundary import BoundaryObservationModel

population_size = 20000
rng = np.random.default_rng()

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))

        self.wheel_distance = 150
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.trans_noise_from_trans = 0.2/100
        self.trans_noise_from_rot = 0.1/100
        self.rot_noise_from_rot = 0.2/100
        self.rot_noise_from_trans = 0.01/100

        self.boundary_model = BoundaryObservationModel()

    def apply_observational_models(self):
        return self.boundary_model.calculate_weights(self.poses)

    def convert_encoders_to_motion(self, left_distance_delta, right_distance_delta):
        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            return left_distance_delta, 0

        mid_distance = (left_distance_delta + right_distance_delta) / 2
        theta = (right_distance_delta - left_distance_delta) / self.wheel_distance

        return mid_distance, theta

    def randomise_motion(self, translation, rotation):
        trans_scale = self.trans_noise_from_trans * abs(translation) \
            + self.trans_noise_from_rot * abs(rotation)
        rot_scale = self.rot_noise_from_rot * abs(rotation) \
            + self.rot_noise_from_trans * abs(translation)

        trans_samples = rng.normal(translation, trans_scale, population_size)
        rot_samples = rng.normal(rotation, rot_scale, population_size)

        return trans_samples, rot_samples

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        left_distance_delta = (distance_data['left_distance'] -
                               self.previous_left_distance)
        right_distance_delta = (distance_data['right_distance'] -
                                self.previous_right_distance)
        self.previous_left_distance = distance_data['left_distance']
        self.previous_right_distance = distance_data['right_distance']

        # Think
        translation, theta = self.convert_encoders_to_motion(
            left_distance_delta, right_distance_delta)
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(
            translation, rotation)
        self.poses = self.poses.move(rot_samples, trans_samples)
        weights = self.apply_observational_models()

        # Act
        publish_sample = self.poses.resample(weights, 200)
        self.poses = self.poses.resample(weights, population_size)
        self.publish_poses(client, publish_sample)

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect()
        arena.publish_map(client)

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)

        while True:
            time.sleep(0.1)

service = Localisation()
service.start()
