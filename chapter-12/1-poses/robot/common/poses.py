import numpy as np


def rotated_poses(poses, rotation):
    return poses + [0, 0, rotation]


## Ideas for initial pose experiments:
# Displaying the pose - show in Javascript
# Rotate
# Translate
# Rotate


def translated_poses(poses, length):
    translated_poses = np.copy(poses)
    translated_poses[:, 0] += np.cos(translated_poses[:, 2]) * length
    translated_poses[:, 1] += np.sin(translated_poses[:, 2]) * length

    return translated_poses
