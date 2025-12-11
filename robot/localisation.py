import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import Pose, rotated_poses, translated_poses

class Localisation:
    def __init__(self):
        self.poses = np.array([(500, 500, 0), (150, 100, np.pi / 3)], dtype=Pose)
        self.poses = np.append(self.poses, rotated_poses(self.poses, np.pi/2), 0)
        self.poses = translated_poses(self.poses, 100)

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def start(self):
        client = connect()
        self.publish_poses(client, self.poses)
        client.loop_stop()

service = Localisation()
service.start()
