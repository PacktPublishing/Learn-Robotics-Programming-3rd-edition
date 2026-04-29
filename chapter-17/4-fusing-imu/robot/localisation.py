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
imu_rotation_influence = 0.7


class EncoderMotionData:
    def __init__(self):
        self.wheel_distance = 136

        self.previous_left_distance = 0
        self.previous_right_distance = 0
        self.pending_theta = 0.0
        self.pending_distance = 0.0

    def on_encoders_data(self, client, userdata, msg):
        encoder_data = json.loads(msg.payload)
        left_distance_delta = (encoder_data['left_distance'] -
                               self.previous_left_distance)
        right_distance_delta = (encoder_data['right_distance'] -
                                self.previous_right_distance)
        self.previous_left_distance = encoder_data['left_distance']
        self.previous_right_distance = encoder_data['right_distance']

        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            self.pending_distance += left_distance_delta
            return

        self.pending_distance += (left_distance_delta + right_distance_delta) / 2
        self.pending_theta += (right_distance_delta - left_distance_delta) / self.wheel_distance

    def consume_data(self):
        translation = self.pending_distance
        theta = self.pending_theta
        self.pending_distance = 0.0
        self.pending_theta = 0.0
        return translation, theta

class ImuMotionData:
    def __init__(self):
        self.previous_yaw = None
        self.pending_theta = 0.0

    def normalize_angle(self, angle):
        return (angle + np.pi) % (2 * np.pi) - np.pi

    def on_imu_data(self, client, userdata, msg):
        imu_data = json.loads(msg.payload)
        yaw = imu_data['yaw']
        if self.previous_yaw is not None:
            delta_yaw = self.normalize_angle(yaw - self.previous_yaw)
            self.pending_theta += delta_yaw
        self.previous_yaw = yaw

    def on_status_update(self, client, userdata, message):
        status = json.loads(message.payload)
        if status['sys'] == 3: # Fully calibrated
            client.subscribe("sensors/imu/euler")
            client.message_callback_add("sensors/imu/euler", self.on_imu_data)

    def consume_data(self):
        delta_theta = self.pending_theta
        self.pending_theta = 0.0
        return delta_theta

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))
        self.weights = np.ones(population_size) / population_size

        self.trans_noise_from_trans = 0.01/100
        self.trans_noise_from_rot = 0.05/100
        self.rot_noise_from_rot = 0.2/100
        self.rot_noise_from_trans = 0.175/100

        self.boundary_model = BoundaryObservationModel()
        self.distance_model = DistanceObservationModel()
        self.encoder_data = EncoderMotionData()
        self.imu_data = ImuMotionData()

    def apply_observational_models(self):
        boundary_weights = self.boundary_model.calculate_weights(self.poses) ** boundary_model_influence
        distance_weights = self.distance_model.calculate_weights(self.poses) ** distance_model_influence
        return boundary_weights * distance_weights

    def calculate_ess(self):
        return 1 / np.sum(self.weights ** 2)

    def randomise_motion(self, translation, rotation):
        trans_scale = self.trans_noise_from_trans * abs(translation) \
            + self.trans_noise_from_rot * abs(rotation)
        rot_scale = self.rot_noise_from_rot * abs(rotation) \
            + self.rot_noise_from_trans * abs(translation)

        trans_samples = rng.normal(translation, trans_scale, population_size)
        rot_samples = rng.normal(rotation, rot_scale, population_size)

        return trans_samples, rot_samples

    def update(self, client):
        # Sense
        translation, encoder_theta = self.encoder_data.consume_data()
        imu_theta = self.imu_data.consume_data()

        # Think
        theta = (1 - imu_rotation_influence) * encoder_theta + imu_rotation_influence * imu_theta
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(
            translation, rotation)

        self.poses = self.poses.move(rot_samples, trans_samples)
        self.weights *= self.apply_observational_models()
        weight_sum = np.sum(self.weights)
        self.weights /= weight_sum
        ess = self.calculate_ess()

        # Act
        if ess < ess_threshold:
            self.poses = self.poses.resample(self.weights, population_size)
            self.weights = np.ones(population_size) / population_size

        publish_sample = self.poses.resample(self.weights, 200)
        self.publish_poses(client, publish_sample)
        publish_json(client, "localisation/ess", {"ess": ess})

    def on_distance_readings(self, client, userdata, msg):
        sensor_data = np.array(json.loads(msg.payload))
        sensor_readings = sensor_data.reshape((8, 8))
        self.distance_model.handle_sensor_readings(sensor_readings)

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect(start_loop=False)
        arena.publish_map(client)

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.encoder_data.on_encoders_data)
        client.subscribe("sensors/imu/status")
        client.message_callback_add("sensors/imu/status", self.imu_data.on_status_update)
        client.publish("launcher/start", "imu_service")

        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm",
                                    self.on_distance_readings)
        client.publish("sensors/distance/control/start_ranging", "")

        try:
            while True:
                client.loop(0.2)
                self.update(client)
        finally:
            client.publish("launcher/stop", "imu_service")

service = Localisation()
service.start()
