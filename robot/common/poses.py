import numpy as np

Pose = np.dtype([('x', np.float32), ('y', np.float32), ('theta', np.float32)])

def rotated_poses(poses, rotation):
    result = np.empty(poses.shape, dtype=Pose)
    result['x'] = poses['x']
    result['y'] = poses['y']
    result['theta'] = poses['theta'] + rotation
    return result

def translated_poses(poses, length):
    result = np.empty(poses.shape, dtype=Pose)
    result['x'] = poses['x'] + np.cos(poses['theta']) * length
    result['y'] = poses['y'] + np.sin(poses['theta']) * length
    result['theta'] = poses['theta']
    return result
