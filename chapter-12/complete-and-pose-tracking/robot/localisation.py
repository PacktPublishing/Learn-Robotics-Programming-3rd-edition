import json
import time

import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Poses
from observation_models.boundary import BoundaryObservationModel

population_size = 20
rng = np.random.default_rng()

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))
        self.weights = np.full(population_size, 1.0 / population_size)
        self.localisation_seq = 0

        self.wheel_distance = 136
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.trans_noise_from_trans = 0.05/100
        self.trans_noise_from_rot = 0.025/100
        self.rot_noise_from_rot = 0.1/100
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

    def resample(self) -> np.ndarray:
        resampled_poses, parent_indices = self.poses.resample(self.weights, population_size)
        self.poses = resampled_poses.view(Poses)
        self.weights.fill(1.0 / population_size)
        return parent_indices.astype(np.int64)

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        source_encoder_seq = distance_data.get('seq')
        source_encoder_timestamp_ms = distance_data.get('timestamp_ms')
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
        self.poses = self.poses.move(rot_samples, trans_samples).view(Poses)
        observation_likelihoods = self.apply_observational_models()
        self.weights = self.weights * observation_likelihoods
        total_weight = np.sum(self.weights)
        if total_weight <= 0.0:
            self.weights.fill(1.0 / population_size)
        else:
            self.weights = self.weights / total_weight

        resample_indices = self.resample().tolist()
        self.localisation_seq += 1
        localisation_timestamp_ms = int(time.time() * 1000)

        # Act
        publish_sample = self.poses
        self.publish_poses(
            client,
            publish_sample,
            self.localisation_seq,
            localisation_timestamp_ms,
            source_encoder_seq,
            source_encoder_timestamp_ms,
            resample_indices,
        )

    def publish_poses(self, client, poses, seq, timestamp_ms, source_encoder_seq, source_encoder_timestamp_ms, resample_indices):
        poses_payload = poses.tolist()
        payload = {
            "seq": seq,
            "timestamp_ms": timestamp_ms,
            "pose_count": int(len(poses_payload)),
            "source_encoder_seq": source_encoder_seq,
            "source_encoder_timestamp_ms": source_encoder_timestamp_ms,
            "resample_indices": resample_indices,
            "poses": poses_payload,
        }
        publish_json(client, "localisation/poses", payload)

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
