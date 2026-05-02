import numpy as np

rng = np.random.default_rng()

class Poses(np.ndarray):
    Pose = np.dtype([('x', np.float32), ('y', np.float32), ('theta', np.float32)])

    def __new__(cls, input_array):
        return np.asarray(input_array, dtype=cls.Pose).view(cls)

    @classmethod
    def generate(cls, count, x_range, y_range, theta_range) -> 'Poses':
        poses = np.empty((count,), dtype=cls.Pose)
        poses['x'] = rng.uniform(x_range[0], x_range[1], count)
        poses['y'] = rng.uniform(y_range[0], y_range[1], count)
        poses['theta'] = rng.uniform(theta_range[0], theta_range[1], count)
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

    def move(self, rotation, translation) -> 'Poses':
        return self.rotate(rotation) \
            .translate(translation) \
            .rotate(rotation)

    def resample(self, weights, sample_count) -> 'Poses':
        cumulative_sum = np.cumsum(weights)
        total_weight = cumulative_sum[-1]
        interval = total_weight / sample_count

        start = rng.uniform(0, interval)
        sample_points = start + np.arange(sample_count) * interval
        indices = np.searchsorted(cumulative_sum, sample_points)

        return self[indices]
