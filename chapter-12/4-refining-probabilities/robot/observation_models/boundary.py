import numpy as np

from common import arena

low_probability = 10 ** -10


class BoundaryObservationModel:
    def in_boundary(self, poses):
        inside_walls = np.logical_and(
            np.logical_and(poses['x'] > arena.left, poses['x'] < arena.right),
            np.logical_and(poses['y'] > arena.bottom, poses['y'] < arena.top)
        )
        not_in_cutouts = np.logical_not(
            np.logical_and(poses['x'] > arena.cutout_left, poses['y'] < arena.cutout_top)
        )
        return np.logical_and(inside_walls, not_in_cutouts)

    def calculate_weights(self, poses):
        return np.where(self.in_boundary(poses), 1.0, low_probability)
