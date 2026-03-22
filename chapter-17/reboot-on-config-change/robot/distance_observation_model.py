import json
import numpy as np

class DistanceObservationModel:
    def __init__(self):
        print("Loading distance probability field...")
        self.probability_field = np.load("robot/distance_probabilities.npy")
        self.margin = 100
        self.middle_to_sensor = [50, 0]  # mm vector from robot center to sensor
        fov_w = np.pi / 4 # radians
        self.w_segments = np.linspace(-fov_w/2, fov_w/2, 8) # 8 segments horizontally
        self.pick_row = 3  # Pick a row in the middle of the sensor
        # the angle is fixed
        self.polar_middle_to_sensor = (0, 50)  # (angle, distance) in mm
        self.latest_readings = np.full_like(self.w_segments, dtype=object)  # (angle, distance) pairs

    def setup(self, mqtt_client):
        mqtt_client.subscribe("sensors/distance/data")
        mqtt_client.message_callback_add("sensors/distance/data",
                                          self.handle_distance)

    def handle_distance(self, client, userdata, message):
        """We have a whole array of distance readings.
        Each reading is a distance in mm to the nearest obstacle in a 2D plane.
        Return polar (angle, distance) vectors from the robot center to each reading.
        """
        sensor_data = np.array(json.loads(message.payload))
        grid = np.fliplr(sensor_data.reshape((8, 8)))
        distances = grid[self.pick_row, :]
        # Create a set of polar vectors from the robot center to each distance reading 
        vectors = [
            self.polar_middle_to_sensor + (angle, dist)
            for angle, dist in zip(self.w_segments, distances)
        ]
        self.latest_readings = np.array(vectors)

    def observational_model(self, poses):
        # strategy - we have 8 readings
        # we can take each reading
        # then transform the poses with it
        # then apply the poses to the probability field
        # store the 8
        # multiply the 8 to get the result for each pose.


        # For each pose
        # combine with the latest readings
        # then validate the resulting vectors against the probability field
        # then multiply the probabilities for each reading
        weights = np.ones(poses.shape[0])
        for reading in self.latest_readings:

    # def observational_model(self, poses):
    #     map_indexes = poses[:, :2] + self.margin
    #     x_indices = np.clip(map_indexes[:, 0].astype(int), 0, self.probability_field.shape[1] - 1)
    #     y_indices = np.clip(map_indexes[:, 1].astype(int), 0, self.probability_field.shape[0] - 1)
    #     weights = self.probability_field[y_indices, x_indices]
    #     return weights