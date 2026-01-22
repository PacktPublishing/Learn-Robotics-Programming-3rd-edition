import json
import numpy as np

class DistanceObservationModel:
    def __init__(self):
        print("Loading distance probability field...")
        self.probability_field = np.load("robot/distance_probabilities.npy")
        self.margin = 100
        fov_w = np.pi / 4 # radians
        self.w_segments = np.linspace(-fov_w/2, fov_w/2, 8) # 8 segments horizontally
        self.pick_row = 3  # Pick a row in the middle of the sensor
        # the angle is fixed
        self.polar_middle_to_sensor = (0, 50)  # (angle, distance) in mm from robot center to sensor
        self.target_positions = np.zeros_like(self.w_segments, dtype=object)  # (angle, distance) pairs

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
        self.target_positions = np.array(vectors)

    def observational_model(self, poses):
        # strategy - we have 8 readings
        # we can take each reading
        # then transform the poses with it
        # then apply the poses to the probability field
        # store the 8
        # multiply the 8 to get the result for each pose.
        weights = np.ones([poses.shape[0], self.target_positions.shape[0]])
        for n, (angle, distance) in enumerate(self.target_positions):
            # use pose theta with the sensor angle
            angles = poses[:, 2] + angle
            # Normalize angles to [-pi, pi]
            angles = (angles + np.pi) % (2 * np.pi) - np.pi
            # Convert polar to Cartesian
            sensed_positions = np.zeros((poses.shape[0], 2))
            sensed_positions[:, 0] = distance * np.cos(angles)
            sensed_positions[:, 1] = distance * np.sin(angles)
            # Add to the poses
            sensed_positions += poses[:, :2]
            # Get the weights from the probability field
            sensor_x = sensed_positions[:, 0] + self.margin
            sensor_y = sensed_positions[:, 1] + self.margin
            weights[:, n] = self.probability_field[sensor_y, sensor_x]
        # Now multiply the weights across all readings
        final_weights = np.prod(weights, axis=1)
        return final_weights
