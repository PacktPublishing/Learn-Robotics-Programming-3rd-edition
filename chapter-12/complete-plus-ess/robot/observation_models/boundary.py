import numpy as np

from common import arena

low_probability = 0.1
crosshair_radius = 50.0  # mm on each side of boundary
crosshair_points = np.array(
    [
        [0.0, 0.0],
        [crosshair_radius, 0.0],
        [-crosshair_radius, 0.0],
        [0.0, crosshair_radius],
        [0.0, -crosshair_radius],
    ],
    dtype=np.float32,
)

Pose2D = np.dtype([('x', np.float32), ('y', np.float32)])


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
        return self.observe_crosshair(poses)

    def observe_crosshair(self, poses):
        crosshair_positions = (
            poses.positions[:, np.newaxis, :] + crosshair_points[np.newaxis, :, :]
        )

        flat_positions = crosshair_positions.reshape(-1, 2)
        samples = np.empty(flat_positions.shape[0], dtype=Pose2D)
        samples['x'] = flat_positions[:, 0]
        samples['y'] = flat_positions[:, 1]

        flat_weights = np.where(self.in_boundary(samples), 1.0, low_probability)
        all_weights = flat_weights.reshape(-1, crosshair_points.shape[0])

        return np.mean(all_weights, axis=1)
