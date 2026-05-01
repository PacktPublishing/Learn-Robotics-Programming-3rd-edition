import numpy as np

class Poses(np.ndarray):
    Pose = np.dtype([('x', np.float32), ('y', np.float32), ('theta', np.float32)])

    def __new__(cls, input_array):
        return np.asarray(input_array, dtype=cls.Pose).view(cls)

    @classmethod
    def generate(cls, count, x_range, y_range, theta_range) -> 'Poses':
        poses = np.empty((count,), dtype=cls.Pose)
        poses['x'] = np.random.uniform(x_range[0], x_range[1], count)
        poses['y'] = np.random.uniform(y_range[0], y_range[1], count)
        poses['theta'] = np.random.uniform(theta_range[0], theta_range[1], count)
        return poses.view(cls)

    def rotate(self, rotation) -> 'Poses':
        result = self.copy()
        result['theta'] += rotation
        return result

    def translate(self, length) -> 'Poses':
        result = self.copy()
        result['x'] += np.cos(self['theta']) * length
        result['y'] += np.sin(self['theta']) * length
        return result

    def append(self, other) -> 'Poses':
        return np.concatenate([self, other]).view(Poses)
