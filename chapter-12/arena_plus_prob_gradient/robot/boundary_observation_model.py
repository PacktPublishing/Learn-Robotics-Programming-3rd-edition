import numpy as np

from common import arena

low_probability = 10 ** -10
boundary_region = 50.0  # mm on each side of boundary


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
        return self.boundary_probability(poses)

    def boundary_probability(self, poses):
        # Calculate distance from each boundary edge (positive = inside)
        dist_left = poses['x'] - arena.left
        dist_right = arena.right - poses['x']
        dist_bottom = poses['y'] - arena.bottom
        dist_top = arena.top - poses['y']

        # For the cutout, calculate distance (negative = inside cutout)
        # Only relevant if x > cutout_left and y < cutout_top
        in_cutout_region = np.logical_and(
            poses['x'] > arena.cutout_left - boundary_region,
            poses['y'] < arena.cutout_top + boundary_region
        )
        dist_from_cutout_x = poses['x'] - arena.cutout_left  # negative when in cutout
        dist_from_cutout_y = arena.cutout_top - poses['y']  # negative when above cutout
        # For cutout, we want the minimum of both distances (most constraining)
        dist_cutout = np.where(
            in_cutout_region,
            np.minimum(dist_from_cutout_x, dist_from_cutout_y),
            boundary_region + 1  # Far from cutout, don't affect probability
        )

        # Find the minimum distance to any boundary (most constraining)
        min_dist = np.minimum.reduce([
            dist_left, dist_right, dist_bottom, dist_top, dist_cutout
        ])

        # Convert distance to weight with gradient:
        # Clamp at -boundary_region (far outside) and add offset
        # Results in weights from 0 (outside) to 2*boundary_region (deep inside)
        # Normalization will happen later, so absolute scale doesn't matter
        weights = np.maximum(min_dist + boundary_region, low_probability)
        return weights
