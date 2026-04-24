import json
import time

import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Poses
from observation_models.boundary import BoundaryObservationModel
from observation_models.distance import DistanceObservationModel

population_size = 20000
ess_threshold = population_size // 10
rng = np.random.default_rng()
boundary_model_influence = 0.5
distance_model_influence = 0.5

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))

        self.wheel_distance = 136
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.trans_noise_from_trans = 0.2/100
        self.trans_noise_from_rot = 0.1/100
        self.rot_noise_from_rot = 0.2/100
        self.rot_noise_from_trans = 0.05/100

        self.boundary_model = BoundaryObservationModel()
        self.distance_model = DistanceObservationModel()

        self.weights = np.ones(population_size) / population_size
        self.step = 0

    def apply_observational_models(self):
        boundary_weights = self.boundary_model.calculate_weights(self.poses) ** boundary_model_influence
        distance_weights = self.distance_model.calculate_weights(self.poses) ** distance_model_influence
        return boundary_weights * distance_weights

    def calculate_ess(self):
        return 1 / np.sum(self.weights ** 2)

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
        self.weights *= self.apply_observational_models()
        weight_sum = np.sum(self.weights)
        if not np.isfinite(weight_sum) or weight_sum == 0:
            self.weights = np.ones(population_size) / population_size
        else:
            self.weights /= weight_sum
        ess = float(self.calculate_ess())
        publish_json(client, "localisation/ess", {"ess": ess})

        # Act
        if ess < ess_threshold:
            self.poses = self.poses.resample(self.weights, population_size)
            self.weights = np.ones(population_size) / population_size

        publish_sample = self.poses.resample(self.weights, 200)
        self.publish_poses(client, publish_sample)

    def on_distance_readings(self, client, userdata, msg):
        sensor_data = np.array(json.loads(msg.payload))
        sensor_readings = sensor_data.reshape((8, 8))
        self.distance_model.handle_sensor_readings(sensor_readings)

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect()
        arena.publish_map(client)

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm",
                                    self.on_distance_readings)
        client.publish("sensors/distance/control/start_ranging", "")

        while True:
            time.sleep(0.1)

service = Localisation()
service.start()
