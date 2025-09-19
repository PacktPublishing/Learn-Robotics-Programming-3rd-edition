import numpy as np

class BoundaryObservationModel:
    def __init__(self):
        self.probability_field = np.load("robot/boundary_probabilities.npy")
        self.margin = 100

    def observational_model(self, poses):
        map_indexes = poses[:, :2] + self.margin
        x_indices = np.clip(map_indexes[:, 0].astype(int), 0, self.probability_field.shape[1] - 1)
        y_indices = np.clip(map_indexes[:, 1].astype(int), 0, self.probability_field.shape[0] - 1)
        weights = self.probability_field[y_indices, x_indices]
        return weights
