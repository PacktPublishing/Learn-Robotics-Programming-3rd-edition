import numpy as np

from common import arena
from common.poses import Poses


class DistanceObservationModel:
    def __init__(self, probability_field_path="robot/observation_models/distance_map.npy"):
        self.probability_field = np.load(probability_field_path)
        self.low_probability = np.min(self.probability_field)
        self.frame = arena.MapFrame(100)
        self.sensor_forward_offset = 50.0 # mm
        sensor_fov = np.pi / 4  # 45 degrees
        sensor_angles = np.linspace(-sensor_fov / 2, sensor_fov / 2, 8)
        self.sensor_unit_vectors = np.array([
            (np.cos(angle), np.sin(angle))
            for angle in sensor_angles
        ])
        # (x, y) positions of each sensor relative to robot center
        self.relative_sensor_positions = np.zeros((8, 2))

    def get_probabilities(self, world_positions: np.ndarray) -> np.ndarray:
        """Get the boundary proximity probabilities for the given world positions.
        Args:
            world_positions (np.ndarray): An array of shape (N, 2) representing N (x, y) world positions.
        Returns:
            np.ndarray: An array of shape (N,) representing the boundary proximity probabilities for each position.
        """
        map_positions = self.frame.world_to_map(world_positions).astype(int)
        mask = ((map_positions[:, 0] >= 0)
            & (map_positions[:, 0] < self.probability_field.shape[1])
            & (map_positions[:, 1] >= 0)
            & (map_positions[:, 1] < self.probability_field.shape[0]))
        out = np.full(mask.shape, self.low_probability, dtype=float)
        out[mask] = self.probability_field[
            map_positions[mask][:, 1],
            map_positions[mask][:, 0]
        ]
        return out

    def handle_sensor_readings(self, sensor_readings: np.ndarray):
        """Process sensor readings to update internal state if needed.
        Args:
            sensor_readings (np.ndarray): An array of shape (8,8) representing distance readings from sensors.
        """
        # Ignore the first 4 lines (floor)
        without_floor = sensor_readings[4:, :]
        # Take the minimum reading of each column to make the row
        row_reading = np.min(without_floor, axis=0)
        # Calculate the (x, y) positions of each sensor reading relative to robot center
        relative_to_sensor = self.sensor_unit_vectors * row_reading[:, np.newaxis]
        # Add the forward offset
        self.relative_sensor_positions = relative_to_sensor + np.array([self.sensor_forward_offset, 0])

    def sensor_endpoints(self, poses: Poses) -> np.ndarray:
        """Project the given poses onto the sensor readings to get expected sensor readings for each pose.
        Args:
            poses (Poses): A Poses object containing the robot's poses.
        Returns:
            np.ndarray: An array of shape (N, 8, 2) representing the expected sensor reading coordinates,
                        where N is the number of poses, 8 is the number of sensors, and 2 is (x, y) coordinates.
        """
        # Calculate the rotation matrix for each pose based on its orientation
        cos_theta = np.cos(poses['theta'])[:, None]
        sin_theta = np.sin(poses['theta'])[:, None]

        sensor_x = self.relative_sensor_positions[None, :, 0]
        sensor_y = self.relative_sensor_positions[None, :, 1]

        sensor_rotated = np.stack(
            (sensor_x * cos_theta - sensor_y * sin_theta,
             sensor_x * sin_theta + sensor_y * cos_theta),
            axis=-1
        ) # shape (N, 8, 2)

        return poses.positions[:, None] + sensor_rotated  # shape (N, 8, 2)

    def calculate_weights(self, poses: Poses) -> np.ndarray:
        """Given a set of poses, use the last set of measurements
        to determine the pose weights.
        Pose weights are based on projecting all the sensors against the loaded probability_field,
        and for each pose, multiplying these.
        """
        endpoints = self.sensor_endpoints(poses)
        flat = endpoints.reshape(-1, 2)
        flat_probs = self.get_probabilities(flat)
        probs = flat_probs.reshape(len(poses), 8)

        # return np.prod(probs, axis=1)
        return np.mean(probs, axis=1)
