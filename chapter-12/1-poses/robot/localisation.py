import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import Poses

class Localisation:
    def __init__(self):
        self.poses = Poses([(500, 500, 0), (150, 100, np.pi / 3)])
        self.poses = self.poses.append(self.poses.rotate(np.pi/2))
        self.poses = self.poses.append(self.poses.translate(100))

    def publish_poses(self, client):
        publish_json(client, "localisation/poses", self.poses.tolist())

    def start(self):
        client = connect()
        self.publish_poses(client)

service = Localisation()
service.start()
