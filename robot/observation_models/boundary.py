import numpy as np

from common import arena
from common.poses import Poses

low_probability = 10 ** -10
crosshair_radius = 50.0  # mm on each side of boundary

Pose2D = np.dtype([('x', np.float64), ('y', np.float64)])

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
        # return self.observe_crosshair(poses)

    def observe_crosshair(self, poses):
        """Observe a 5 tap crosshair pattern for each pose.
        """
        crosshair_points = np.array([
            [0, 0],
            [crosshair_radius, 0],
            [-crosshair_radius, 0],
            [0, crosshair_radius],
            [0, -crosshair_radius]
        ])  # shape (5, 2)

        # # Expand poses to shape (num_poses, 1, 2) and crosshair to (1, 5, 2)
        # expanded_poses = poses[['x', 'y']][:, np.newaxis, :]  # shape (num_poses, 1, 2)
        # expanded_crosshair = crosshair_points[np.newaxis, :, :]  # shape (1, 5, 2)

        # Calculate absolute positions of crosshair points for each pose
        crosshair_positions = poses.positions[:, np.newaxis, :] + crosshair_points  # shape (num_poses, 5, 2)
        # Make the boundary observation for all points in the crosshair
        # flatten
        flat_positions = crosshair_positions.reshape(-1,2).view(Pose2D)  # shape (num_poses * 5, 2)
        flat_weights = np.where(self.in_boundary(flat_positions), 1.0, low_probability)
        all_weights=flat_weights.reshape(-1, 5)  # shape (num_poses, 5)
        # Create a mean weight for each pose based on the crosshair points
        return np.mean(all_weights, axis=1)  # shape (num_poses,)
