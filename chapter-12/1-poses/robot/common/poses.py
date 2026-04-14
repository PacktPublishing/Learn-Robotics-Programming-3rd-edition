import numpy as np

class Poses(np.ndarray):
    Pose = np.dtype([('x', np.float32), ('y', np.float32), ('theta', np.float32)])

    def __new__(cls, input_array):
        return np.asarray(input_array, dtype=cls.Pose).view(cls)

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
