import json
import time

import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Pose, rotated_poses, translated_poses
from boundary_observation_model import BoundaryObservationModel

population_size = 20000
rng = np.random.default_rng()
low_probability = 10 ** -10
resample_random_ratio = 0.02  # 2% random poses on resample

class Localisation:
    def generate_random_poses(self, count):
        """Generate random poses within the arena boundaries."""
        poses = np.empty((count,), dtype=Pose)
        poses['x'] = rng.uniform(arena.left, arena.right, count)
        poses['y'] = rng.uniform(arena.bottom, arena.top, count)
        poses['theta'] = rng.uniform(0, 2 * np.pi, count)
        return poses

    def __init__(self):
        self.poses = self.generate_random_poses(rng, population_size)

        self.wheel_distance = 0
        self.config_ready = False
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.trans_noise_from_trans = 2.0/100
        self.trans_noise_from_rot = 1.0/100
        self.rot_noise_from_rot = 2/100
        self.rot_noise_from_trans = 0.2/100

        self.boundary_model = BoundaryObservationModel()

    def apply_observational_models(self):
        return self.boundary_model.calculate_weights(self.poses)

    def resample_poses(self, weights, sample_count, random_ratio):
        """Resample poses based on weights.

        Args:
            weights: Weight for each pose
            sample_count: Number of poses to return
            inject_random: If True, inject random poses to maintain diversity
            random_ratio: Proportion of random poses to inject (e.g., 0.02 = 2%)
        """
        normalised_weights = weights / np.sum(weights)

        if random_ratio <= 0:
            resample_count = sample_count
        else:
            # Resample most particles from existing population
            resample_count = int(sample_count * (1.0 - random_ratio))

        resampled = rng.choice(
            self.poses,
            size=resample_count,
            p=normalised_weights
        )

        random_count = sample_count - resample_count
        if random_count == 0:
            return resampled

        # Inject random valid poses to maintain diversity
        random_poses = self.generate_random_poses(random_count)

        return np.concatenate([resampled, random_poses])

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
        left_distance_delta = distance_data['left_distance'] - self.previous_left_distance
        right_distance_delta = distance_data['right_distance'] - self.previous_right_distance
        self.previous_left_distance = distance_data['left_distance']
        self.previous_right_distance = distance_data['right_distance']

        # Think
        translation, theta = self.convert_encoders_to_motion(left_distance_delta, right_distance_delta)
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(translation, rotation)
        self.move_poses(rot_samples, trans_samples)
        weights = self.apply_observational_models()

        # Act
        self.poses = self.resample_poses(weights, population_size, random_ratio=resample_random_ratio)
        publish_sample = self.resample_poses(weights, 200, random_ratio=0)
        self.publish_poses(client, publish_sample)

    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        print(data)
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect()
        arena.publish_map(client)
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
