import json
import time

import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Poses
from observation_models.boundary import BoundaryObservationModel
from observation_models.distance import DistanceObservationModel

population_size = 20000
ess_resample_ratio_threshold = 0.5
rng = np.random.default_rng()

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))
        self.weights = np.full(population_size, 1.0 / population_size)
        self.localisation_seq = 0

        self.wheel_distance = 136 #161
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.trans_noise_from_trans = 0.2/100
        self.trans_noise_from_rot = 0.1/100
        self.rot_noise_from_rot = 0.4/100
        self.rot_noise_from_trans = 0.04/100

        self.boundary_model = BoundaryObservationModel()
        self.distance_model = DistanceObservationModel()

    def effective_sample_size(self, weights: np.ndarray) -> float:
        """Return Effective Sample Size (ESS) for the current particle weights.

        ESS is a measure of how diverse the particle weights are:
            ESS = 1 / sum(normalized_weight^2)

        Interpretation:
        - High ESS (near particle count): weights are spread out (high diversity).
        - Low ESS: a small number of particles dominate (low diversity / overconfidence risk).
        """
        total_weight = np.sum(weights)
        if total_weight <= 0:
            return 0.0
        normalized = weights / total_weight
        sum_squared = np.sum(normalized * normalized)
        if sum_squared <= 0:
            return 0.0
        return float(1.0 / sum_squared)

    def ess_status(self, ess: float) -> str:
        ess_ratio = ess / population_size
        if ess_ratio < 0.1:
            return "low"
        if ess_ratio < 0.5:
            return "medium"
        return "high"

    def should_resample(self, ess: float) -> bool:
        return ess < (population_size * ess_resample_ratio_threshold)

    def pose_spread_metrics(self) -> tuple[float, float]:
        x = self.poses['x'].astype(np.float64)
        y = self.poses['y'].astype(np.float64)
        theta = self.poses['theta'].astype(np.float64)
        weights = self.weights

        mean_x = np.sum(weights * x)
        mean_y = np.sum(weights * y)
        var_x = np.sum(weights * (x - mean_x) ** 2)
        var_y = np.sum(weights * (y - mean_y) ** 2)
        spread_xy_mm = float(np.sqrt(var_x + var_y))

        mean_sin = np.sum(weights * np.sin(theta))
        mean_cos = np.sum(weights * np.cos(theta))
        resultant_length = float(np.hypot(mean_sin, mean_cos))
        resultant_length = max(resultant_length, 1e-12)
        theta_circular_std_rad = float(np.sqrt(-2.0 * np.log(resultant_length)))
        spread_theta_deg = float(np.degrees(theta_circular_std_rad))

        return spread_xy_mm, spread_theta_deg

    def apply_observational_models(self):
        boundary_weights = self.boundary_model.calculate_weights(self.poses)
        distance_weights = 1 # self.distance_model.calculate_weights(self.poses)
        return boundary_weights * distance_weights

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
        self.poses = self.poses.move(rot_samples, trans_samples)
        observation_likelihoods = self.apply_observational_models()
        self.weights = self.weights * observation_likelihoods
        total_weight = np.sum(self.weights)
        if total_weight <= 0.0:
            self.weights.fill(1.0 / population_size)
        else:
            self.weights = self.weights / total_weight

        in_bounds_ratio = float(np.mean(self.boundary_model.in_boundary(self.poses)))
        ess = self.effective_sample_size(self.weights)
        spread_xy_mm, spread_theta_deg = self.pose_spread_metrics()
        resample_triggered = self.should_resample(ess)
        self.localisation_seq += 1
        localisation_timestamp_ms = int(time.time() * 1000)

        # Act
        publish_sample = self.poses.resample(self.weights, 200)
        if resample_triggered:
            self.poses = self.poses.resample(self.weights, population_size)
            self.weights.fill(1.0 / population_size)

        self.publish_poses(
            client,
            publish_sample,
            self.localisation_seq,
            localisation_timestamp_ms,
            source_encoder_seq,
            source_encoder_timestamp_ms
        )
        self.publish_diagnostics(
            client,
            {
                "seq": self.localisation_seq,
                "timestamp_ms": localisation_timestamp_ms,
                "source_encoder_seq": source_encoder_seq,
                "source_encoder_timestamp_ms": source_encoder_timestamp_ms,
                "translation_mm": float(translation),
                "theta_rad": float(theta),
                "rotation_rad": float(rotation),
                "in_bounds_ratio": in_bounds_ratio,
                "effective_sample_size": ess,
                "ess_ratio": float(ess / population_size),
                "ess_status": self.ess_status(ess),
                "pose_spread_xy_mm": spread_xy_mm,
                "pose_spread_theta_deg": spread_theta_deg,
                "resample_triggered": resample_triggered,
                "ess_resample_ratio_threshold": ess_resample_ratio_threshold,
            }
        )

    def on_distance_readings(self, client, userdata, msg):
        sensor_data = np.array(json.loads(msg.payload))
        sensor_readings = sensor_data.reshape((8, 8))
        self.distance_model.handle_sensor_readings(sensor_readings)

    def publish_poses(self, client, poses, seq, timestamp_ms, source_encoder_seq, source_encoder_timestamp_ms):
        publish_json(client, "localisation/poses", poses.tolist())
        publish_json(client, "localisation/poses_meta", {
            "seq": seq,
            "timestamp_ms": timestamp_ms,
            "pose_count": int(len(poses)),
            "source_encoder_seq": source_encoder_seq,
            "source_encoder_timestamp_ms": source_encoder_timestamp_ms,
        })

    def publish_diagnostics(self, client, diagnostics):
        publish_json(client, "localisation/diagnostics", diagnostics)

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
