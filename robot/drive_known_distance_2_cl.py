import ujson as json
import time

from common.mqtt_behavior import connect, publish_json

class DriveKnownDistanceBehavior:
    def __init__(self):
        self.left_distance = 0
        self.right_distance = 0
        self.has_encoder_data = False

    def on_encoders_data(self, client, userdata, msg):
        distance_data = json.loads(msg.payload)
        self.left_distance = distance_data['left_distance']
        self.right_distance = distance_data['right_distance']
        self.has_encoder_data = True

    def drive_line(self, client, expected_distance=1000, speed=100):
        start_left_distance = self.left_distance
        start_right_distance = self.right_distance
        distance_reached = False
        while not distance_reached:
            # Sense
            left_travelled_distance = self.left_distance - start_left_distance
            right_travelled_distance = self.right_distance - start_right_distance
            left_error = expected_distance - left_travelled_distance
            right_error = expected_distance - right_travelled_distance

            # Think
            distance_error = max(left_error, right_error)
            if distance_error < 1:
                distance_reached = True
                current_speed = 0
            else:
                current_speed = speed
            # Act
            publish_json(client, "drive_known_distance/plot", {
                "left_error": left_error,
                "right_error": right_error,
                "time": time.time()
            })
            publish_json(client, "wheel_control/wheel_speed_mm", [current_speed, current_speed])
            time.sleep(0.1)

    def start(self):
        client = connect()
        client.subscribe("sensors/encoders/data")
        publish_json(client, "wheel_control/enabled", True)
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        while not self.has_encoder_data:
            time.sleep(0.05)
        self.drive_line(client)


behavior = DriveKnownDistanceBehavior()
behavior.start()
