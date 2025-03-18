import ujson as json
import time

from common.mqtt_behavior import connect, publish_json

class DriveKnownDistanceBehavior:
    def __init__(self):
        self.left_distance = 0
        self.right_distance = 0

    def on_encoders_data(self, client, userdata, msg):
        # Sense
        distance_data = json.loads(msg.payload)
        self.left_distance = distance_data['left_distance']
        self.right_distance = distance_data['right_distance']

    def drive_line(self, client, expected_distance=1000, speed=0.8):
        distance_reached = False
        while not distance_reached:
            left_error = expected_distance - self.left_distance
            right_error = expected_distance - self.right_distance
            publish_json(client, "drive_known_distance/plot", {
                "left_error": left_error,
                "right_error": right_error,
                "time": time.time()
            })

            # Think
            if abs(left_error) > abs(right_error):
                distance_error = left_error
            else:
                distance_error = right_error
            if distance_error < 1:
                self.distance_reached = True
                current_speed = 0
            else:
                current_speed = speed
            # Act
            publish_json(client, "motors/wheels", [current_speed, current_speed])
            time.sleep(0.1)

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/encoders/data")
        client.publish("sensors/encoders/control/reset")
        client.message_callback_add("sensors/encoders/data",
                                    self.on_encoders_data)
        client.start()
        self.drive_line(client)


behavior = DriveKnownDistanceBehavior()
behavior.start()
