import json
import time

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.poses import Pose, rotated_poses, translated_poses

width = 1500
height = 1500
cutout_left = 1000
cutout_top = 500
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
        self.poses = np.empty((population_size,), dtype=Pose)
        self.poses['x'] = rng.uniform(0, width, population_size)
        self.poses['y'] = rng.uniform(0, height, population_size)
        self.poses['theta'] = rng.uniform(0, 2 * np.pi, population_size)

        self.wheel_distance = 0
        self.config_ready = False
        self.previous_left_distance = 0
        self.previous_right_distance = 0

        self.alpha_trans_trans = 2.0/100  # Increased from 1.2
        self.alpha_trans_rot = 1.0/100     # Increased from 0.5
        self.alpha_rot_rot = 2/100         # Increased from 1
        self.alpha_rot_trans = 0.2/100     # Increased from 0.1

    def boundary_probability(self):
        """Calculate smooth probability gradient at boundaries.
        
        Returns probability 1.0 for poses >50mm inside boundary,
        0.0 for poses >50mm outside boundary,
        and a linear gradient in between.
        """
        boundary_region = 50.0  # mm on each side of boundary
        
        # Calculate distance from each boundary edge (positive = inside)
        dist_left = self.poses['x']
        dist_right = width - self.poses['x']
        dist_bottom = self.poses['y']
        dist_top = height - self.poses['y']
        
        # For the cutout, calculate distance (negative = inside cutout)
        # Only relevant if x > cutout_left and y < cutout_top
        in_cutout_region = np.logical_and(
            self.poses['x'] > cutout_left - boundary_region,
            self.poses['y'] < cutout_top + boundary_region
        )
        dist_from_cutout_x = self.poses['x'] - cutout_left  # negative when in cutout
        dist_from_cutout_y = cutout_top - self.poses['y']  # negative when above cutout
        # For cutout, we want the minimum of both distances (most constraining)
        dist_cutout = np.where(
            in_cutout_region,
            np.minimum(dist_from_cutout_x, dist_from_cutout_y),
            boundary_region + 1  # Far from cutout, don't affect probability
        )
        
        # Find the minimum distance to any boundary (most constraining)
        min_dist = np.minimum.reduce([
            dist_left, dist_right, dist_bottom, dist_top, dist_cutout
        ])
        
        # Convert distance to probability:
        # distance > +50mm: prob = 1.0
        # distance < -50mm: prob = 0.0
        # -50mm < distance < +50mm: linear gradient
        probability = np.clip((min_dist + boundary_region) / (2 * boundary_region), low_probability, 1.0)
        
        return probability

    def observational_model(self):
        weights = self.boundary_probability()
        # Apply low probability floor to avoid division issues
        weights = np.where(weights < low_probability, low_probability, weights)
        return weights

    def generate_valid_random_poses(self, count, margin=50):
        """Generate random poses that are inside the boundary.
        
        Args:
            count: Number of valid poses to generate
            margin: Minimum distance from boundary edges (mm)
        
        Returns:
            Array of valid Pose objects inside the boundary
        """
        random_poses = np.empty((count,), dtype=Pose)
        random_poses['x'] = rng.uniform(0, width, count)
        random_poses['y'] = rng.uniform(0, height, count)
        random_poses['theta'] = rng.uniform(0, 2 * np.pi, count)
        
        # Check which poses are valid (inside boundary with margin)
        def is_valid(poses):
            inside = np.logical_and(
                np.logical_and(poses['x'] > margin, poses['x'] < width - margin),
                np.logical_and(poses['y'] > margin, poses['y'] < height - margin)
            )
            not_in_cutout = np.logical_not(
                np.logical_and(poses['x'] > cutout_left + margin, 
                              poses['y'] < cutout_top - margin)
            )
            return np.logical_and(inside, not_in_cutout)
        
        valid = is_valid(random_poses)
        
        # Regenerate invalid poses until we have enough valid ones
        while np.sum(valid) < count:
            invalid_indices = np.where(~valid)[0]
            random_poses['x'][invalid_indices] = rng.uniform(0, width, len(invalid_indices))
            random_poses['y'][invalid_indices] = rng.uniform(0, height, len(invalid_indices))
            random_poses['theta'][invalid_indices] = rng.uniform(0, 2 * np.pi, len(invalid_indices))
            valid = is_valid(random_poses)
        
        return random_poses

    def resample_poses(self, weights, sample_count, inject_random=False, random_ratio=0.02):
        """Resample poses based on weights.
        
        Args:
            weights: Weight for each pose
            sample_count: Number of poses to return
            inject_random: If True, inject random poses to maintain diversity
            random_ratio: Proportion of random poses to inject (e.g., 0.02 = 2%)
        """
        normalised_weights = weights / np.sum(weights)
        
        if not inject_random or random_ratio <= 0:
            # Simple resampling without random injection
            return rng.choice(
                self.poses,
                size=sample_count,
                p=normalised_weights
            )
        
        # Resample most particles from existing population
        resample_count = int(sample_count * (1.0 - random_ratio))
        random_count = sample_count - resample_count
        
        resampled = rng.choice(
            self.poses,
            size=resample_count,
            p=normalised_weights
        )
        
        # Inject random valid poses to maintain diversity
        random_poses = self.generate_valid_random_poses(random_count, margin=50)
        
        return np.concatenate([resampled, random_poses])

    def convert_encoders_to_motion(self, left_distance_delta, right_distance_delta):
        # Special case, straight line
        if left_distance_delta == right_distance_delta:
            return left_distance_delta, 0

        mid_distance = (left_distance_delta + right_distance_delta) / 2
        theta = (right_distance_delta - left_distance_delta) / self.wheel_distance

        return mid_distance, theta

    def move_poses(self, rotation, translation):
        self.poses = rotated_poses(self.poses, rotation)
        self.poses = translated_poses(self.poses, translation)
        self.poses = rotated_poses(self.poses, rotation)

    def randomise_motion(self, translation, rotation):
        trans_scale = self.alpha_trans_trans * abs(translation) \
            + self.alpha_trans_rot * abs(rotation)
        rot_scale = self.alpha_rot_rot * abs(rotation) \
            + self.alpha_rot_trans * abs(translation)

        trans_samples = rng.normal(translation, trans_scale, population_size)
        rot_samples = rng.normal(rotation, rot_scale, population_size)

        return trans_samples, rot_samples

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        left_distance_delta = distance_data['left_distance'] - self.previous_left_distance
        right_distance_delta = distance_data['right_distance'] - self.previous_right_distance
        self.previous_left_distance = distance_data['left_distance']
        self.previous_right_distance = distance_data['right_distance']

        # Think
        translation, theta = self.convert_encoders_to_motion(left_distance_delta, right_distance_delta)
        rotation = theta / 2
        trans_samples, rot_samples = self.randomise_motion(translation, rotation)
        self.move_poses(rot_samples, trans_samples)
        weights = self.observational_model()
        
        # Diagnostics
        outside_boundary = weights < 0.5
        pct_outside = np.sum(outside_boundary) / len(weights) * 100
        mean_x = np.mean(self.poses['x'])
        mean_y = np.mean(self.poses['y'])
        if pct_outside > 10:  # Log if more than 10% are outside
            print(f"Warning: {pct_outside:.1f}% poses near/outside boundary. Mean pose: ({mean_x:.0f}, {mean_y:.0f})")
        
        self.poses = self.resample_poses(weights, population_size, inject_random=True, random_ratio=0.02)
        # Act - display sampling without random injection
        publish_sample = self.resample_poses(weights, 200, inject_random=False)
        self.publish_poses(client, publish_sample)

    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        print(data)
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def publish_poses(self, client, poses):
        publish_json(client, "localisation/poses", poses.tolist())

    def publish_map(self, client):
        publish_json(client, "localisation/map", {
            "walls": walls
        })

    def start(self):
        client = connect()
        self.publish_map(client)
        print("Published map. Getting wheel distance config...")
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "robot/wheel_distance",
                        ])
        while not self.config_ready:
            time.sleep(0.1)
        print("Configuration received. Starting localisation.")

        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        while True:
            time.sleep(0.1)

service = Localisation()
service.start()
