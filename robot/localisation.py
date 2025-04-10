import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import rotated_poses, translated_poses

walls = [
    (0, 1500),
    (1500, 1500),
    (1500, 500),
    (1000, 500),
    (1000, 0),
    (0, 0)
]
population_size = 200

class Localisation:
    def __init__(self):
        self.poses = np.column_stack((
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 1500, population_size),
            np.random.uniform(0, 2 * np.pi, population_size)
        ))
        self.keep_points_in_boundary()

    def keep_points_in_boundary(self):
        poses_in_bounds = np.logical_not(
            np.logical_and(
                np.greater(self.poses[:, 0], 1000),
                np.less(self.poses[:, 1], 500)
            )
        )
        self.poses = self.poses[poses_in_bounds]

    def publish_poses(self, client):
        publish_json(client, "localisation/poses", self.poses.tolist())

    def publish_map(self, client):
        publish_json(client, "localisation/map", {
            "walls": walls
        })

    def start(self):
        client = connect()
        self.publish_poses(client)
        self.publish_map(client)

service = Localisation()
service.start()
