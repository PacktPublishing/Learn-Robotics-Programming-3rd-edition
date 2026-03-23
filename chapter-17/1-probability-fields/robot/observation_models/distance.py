import numpy as np

from common import arena
from common.poses import Poses


class DistanceObservationModel:
    def __init__(self, probability_field_path="robot/observation_models/distance_map.npy"):
        self.probability_field = np.load(probability_field_path)
        self.low_probability = np.min(self.probability_field)
        self.frame = arena.MapFrame(100)

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

