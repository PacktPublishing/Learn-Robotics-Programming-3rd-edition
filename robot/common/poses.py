import numpy as np


def rotated_poses(poses, rotation):
    return np.column_stack((
            poses[:, 0],
            poses[:, 1],
            poses[:, 2] + rotation
    ))

def translated_poses(poses, length):
    return np.column_stack((
            poses[:, 0] + np.cos(poses[:, 2]) * length,
            poses[:, 1] + np.sin(poses[:, 2]) * length,
            poses[:, 2]
    ))
