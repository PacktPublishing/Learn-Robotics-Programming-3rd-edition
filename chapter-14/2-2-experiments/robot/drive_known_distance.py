import ujson as json
import time

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController
from common.time_stepper import TimeStepper

class DriveKnownDistanceBehavior:
    def __init__(self):
        self.left_distance = 0
        self.right_distance = 0
        self.distance_pid = PIDController(0.2, 0.01)
        self.speed = 180
        self.stopping_distance = 100

    def on_encoders_data(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        self.left_distance = distance_data['left_distance']
        self.right_distance = distance_data['right_distance']

    def drive_line(self, client, expected_distance=1000):
        distance_reached = False
        time_stepper = TimeStepper()
        while not distance_reached:
            # Sense
            left_error = expected_distance - self.left_distance
            right_error = expected_distance - self.right_distance
            time_difference = time_stepper.step()

            # Think
            if abs(left_error) > abs(right_error):
                distance_error = left_error
            else:
                distance_error = right_error
            if distance_error > self.stopping_distance:
                current_speed = self.speed
            elif abs(distance_error) < 1:
                distance_reached = True
                current_speed = 0
            else:
                current_speed = self.distance_pid.control(distance_error, time_difference)
            # Act
            publish_json(client, "drive_known_distance/plot", {
                "left_error": left_error,
                "right_error": right_error,
                "time": time.time()
            })
            publish_json(client, "wheel_control/wheel_speed_mm", [current_speed, current_speed])
            time.sleep(0.1)

    def on_config_updated(self, client, userdata, message):
        data = json.loads(message.payload)
        self.distance_pid.handle_config_messages(data, 'drive_known_distance')
        if 'drive_known_distance/speed' in data:
            self.speed = data['drive_known_distance/speed']
        if 'drive_known_distance/stopping_distance' in data:
            self.stopping_distance = data['drive_known_distance/stopping_distance']


    def start(self):
        client = connect()
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        publish_json(client, "wheel_control/enabled", True)
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.subscribe("config/updated")
        client.message_callback_add("config/updated",
                                    self.on_config_updated)
        publish_json(client, "config/get", [
                        "drive_known_distance/proportional",
                        "drive_known_distance/integral",
                        "drive_known_distance/speed",
                        "drive_known_distance/stopping_distance"])
        self.drive_line(client)

behavior = DriveKnownDistanceBehavior()
behavior.start()
