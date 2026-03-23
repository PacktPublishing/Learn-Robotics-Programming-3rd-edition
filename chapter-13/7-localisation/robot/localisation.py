import atexit
import ujson as json
import time

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import rotated_poses, translated_poses
from common.delta_value import DeltaValue

width = 1200
height = 1800
cutout_left = 900
cutout_top = 800
# width = 1500
# height = 1500
# cutout_left = 1000
# cutout_top = 500

walls = [
    (0, height),
    (width, height),
    (width, cutout_top),
    (cutout_left, cutout_top),
    (cutout_left, 0),
    (0, 0)
]

population_size = 20000
rng = np.random.default_rng()
low_probability = 10 ** -10


class Localisation:
    def __init__(self):
        self.poses = np.column_stack((
            rng.uniform(0, width, population_size),
            rng.uniform(0, height, population_size),
            rng.uniform(0, 2 * np.pi, population_size)
        ))
        self.wheel_distance = 0

        self.alpha_trans_trans = 1.2/100
        self.alpha_trans_rot = 0.5/100
        self.alpha_rot_rot = 2/100
        self.alpha_rot_trans = 0.1/100

        self.config_ready = False
        self.left_distance = DeltaValue()
        self.right_distance = DeltaValue()
        self.yaw = DeltaValue()

    def in_boundary(self):
        inside_walls = np.logical_and(
            np.logical_and(self.poses[:, 0] > 0, self.poses[:, 0] < width),
            np.logical_and(self.poses[:, 1] > 0, self.poses[:, 1] < height)
        )
        not_in_cutouts = np.logical_not(
            np.logical_and(self.poses[:, 0] > cutout_left, self.poses[:, 1] < cutout_top)
        )
        return np.logical_and(inside_walls, not_in_cutouts)

    def observational_model(self):
        weights = np.where(self.in_boundary(), 1.0, low_probability)
        return weights

    def resample_poses(self, weights, sample_count):
        normalised_weights = weights / np.sum(weights)
        return rng.choice(
            self.poses,
            size=sample_count,
            p=normalised_weights
        )

    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def publish_map(self, client):
        publish_json(client, "localisation/map", {
            "walls": walls
        })

    def convert_encoders_to_motion(self, left_distance_delta, right_distance_delta):
        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            return left_distance_delta, 0

        mid_distance = (left_distance_delta + right_distance_delta) / 2
        theta = (right_distance_delta - left_distance_delta) / self.wheel_distance

        return mid_distance, theta

    def randomise_motion(self, translation, rotation):
        trans_scale = self.alpha_trans_trans * abs(translation) \
            + self.alpha_trans_rot * abs(rotation)
        rot_scale = self.alpha_rot_rot * abs(rotation) \
            + self.alpha_rot_trans * abs(translation)
        trans_samples = rng.normal(translation, trans_scale, population_size)
        rot_samples = rng.normal(rotation, rot_scale, population_size)
        return trans_samples, rot_samples

    def move_poses(self, rotation, translation):
        self.poses = rotated_poses(self.poses, rotation)
        self.poses = translated_poses(self.poses, translation)
        self.poses = rotated_poses(self.poses, rotation)

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        self.left_distance.set_current(distance_data['left_distance'])
        self.right_distance.set_current(distance_data['right_distance'])

    def on_imu_data(self, client, userdata, message):
        # Sense
        imu_data = json.loads(message.payload)
        self.yaw.set_current(imu_data['yaw'])

    def fuse_sensors(self, client):
        # Sense
        yaw_delta = self.yaw.consume_delta()
        if yaw_delta > np.pi:
            yaw_delta -= 2 * np.pi
        if yaw_delta < -np.pi:
            yaw_delta += 2 * np.pi
        left_distance_delta = self.left_distance.consume_delta()
        right_distance_delta = self.right_distance.consume_delta()

        # Think
        translation, encoder_theta = self.convert_encoders_to_motion(left_distance_delta, right_distance_delta)
        theta = yaw_delta * 0.7 + encoder_theta * 0.3
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(translation, rotation)
        self.move_poses(rot_samples, trans_samples)
        weights = self.observational_model()
        self.poses = self.resample_poses(weights, population_size)
        # Act
        publish_sample = self.resample_poses(weights, 100)
        self.publish_poses(client, publish_sample)

    def stop(self, client):
        print("Stopping motors")
        publish_json(client, "motors/wheels", [0, 0])
        client.publish("launcher/stop", "imu_service")

    def start(self):
        client = connect()
        self.publish_map(client)
        print("Waiting for config")
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "robot/wheel_distance",
                        ])
        while not self.config_ready:
            time.sleep(0.1)
        print("Config received. Now waiting for sensor data...")

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("sensors/imu/euler")
        client.message_callback_add("sensors/imu/euler", self.on_imu_data)
        client.publish("launcher/start", "imu_service")
        atexit.register(self.stop, client)
        while True:
            self.fuse_sensors(client)
            time.sleep(0.01)

service = Localisation()
service.start()
