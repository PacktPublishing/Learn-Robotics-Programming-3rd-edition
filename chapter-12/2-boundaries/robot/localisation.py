import numpy as np

from common import arena
from common.mqtt_behavior import connect, publish_json
from common.poses import Poses

population_size = 200
rng = np.random.default_rng()

class Localisation:
    def __init__(self):
        self.poses = Poses.generate(population_size, (arena.left, arena.right), (arena.bottom, arena.top), (0, 2 * np.pi))

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect()
        arena.publish_map(client)
        self.publish_poses(client, self.poses)
        client.loop_stop()


service = Localisation()
service.start()
