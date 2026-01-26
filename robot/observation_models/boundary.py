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
        return np.where(self.in_boundary(poses), 1.0, low_probability)

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

        # Convert distance to probability:
        # distance > +50mm: prob = 1.0
        # distance < -50mm: prob = 0.0
        # -50mm < distance < +50mm: linear gradient
        weights = (min_dist + boundary_region) / (2 * boundary_region)
        return np.where(
            weights < low_probability,
            low_probability,
            np.where(weights > 1.0, 1.0, weights)
        )
