import ujson as json
import time
import math

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController
from common.time_stepper import TimeStepper


class BehaviorPath:
    def __init__(self):
        self.left_distance = 0
        self.right_distance = 0
        self.distance_pid = PIDController(0.2, 0.01)
        self.speed = 180
        self.stopping_distance = 100
        self.wheel_distance = 0
        self.config_ready = False

    def on_encoders_data(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        self.left_distance = distance_data['left_distance']
        self.right_distance = distance_data['right_distance']

    def drive_line(self, client, expected_distance=1000):
        self.drive_wheels_to_distance(client, expected_distance, expected_distance)

    def drive_wheels_to_distance(self, client, left_target, right_target):
        left_is_primary = abs(left_target) > abs(right_target)

        speed_factor = 1 / max(abs(left_target), abs(right_target))
        left_factor = left_target * speed_factor
        right_factor = right_target * speed_factor
        publish_json(client, "path/speed_factors", {
            "left_factor": left_factor, "right_factor": right_factor,
            "left_is_primary": left_is_primary
        })
        client.publish("sensors/encoders/control/reset")
        while self.left_distance !=0 and self.right_distance != 0:
            time.sleep(0.01)
        time_stepper = TimeStepper()
        self.distance_pid.reset()
        publish_json(client, "wheel_control/enabled", True)

        distance_reached = False
        while not distance_reached:
            # Sense
            if left_is_primary:
                error = left_target - self.left_distance
            else:
                error = right_target - self.right_distance
            time_difference = time_stepper.step()

            # Think
            if error > self.stopping_distance:
                current_speed = self.speed
            elif abs(error) < 1:
                distance_reached = True
                current_speed = 0
            else:
                current_speed = self.distance_pid.control(error, time_difference)

            left_speed = current_speed * left_factor
            right_speed = current_speed * right_factor

            # Act
            publish_json(client, "path/plot", {
                "error": error, "time": time.time()
            })
            publish_json(client, "wheel_control/wheel_speed_mm", [left_speed, right_speed])
            time.sleep(0.1)

    def drive_curve(self, client, angle_in_degrees, turn_radius):
        angle_in_radians = math.radians(angle_in_degrees)
        # Calculate the radius for each wheel
        left_turn_radius = turn_radius - (self.wheel_distance / 2)
        right_turn_radius = turn_radius + (self.wheel_distance / 2)
        # Calculate the distance for each wheel
        left_turn_distance = angle_in_radians * left_turn_radius
        right_turn_distance = angle_in_radians * right_turn_radius
        publish_json(client, "path/curve", {
            "angle_in_radians": angle_in_radians,
            "left_turn_radius": left_turn_radius, "right_turn_radius": right_turn_radius,
            "left_turn_distance": left_turn_distance, "right_turn_distance": right_turn_distance,
        })
        self.drive_wheels_to_distance(client, left_turn_distance, right_turn_distance)

    def on_config_updated(self, client, userdata, message):
        self.config_ready = True
        data = json.loads(message.payload)
        self.distance_pid.handle_config_messages(data, 'path')
        if 'path/speed' in data:
            self.speed = data['path/speed']
        if 'path/stopping_distance' in data:
            self.stopping_distance = data['path/stopping_distance']
        if 'robot/wheel_distance' in data:
            self.wheel_distance = data['robot/wheel_distance']

    def start(self):
        client = connect()
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "path/proportional",
                        "path/integral",
                        "path/speed",
                        "path/stopping_distance",
                        "robot/wheel_distance",
                        ])
        # Wait for config to be ready
        while not self.config_ready:
            time.sleep(0.1)

        for n in range(4):
            self.drive_line(client, 300)
            self.drive_curve(client, 90, 30)

behavior = BehaviorPath()
behavior.start()
