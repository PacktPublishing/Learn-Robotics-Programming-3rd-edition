import time
import json

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController

center_x = 704 / 2
object_size_ref = 370


class FollowObjectBehavior:
    def __init__(self):
        self.object_x = center_x
        self.object_size = None

    def on_object_detected(self, client, userdata, msg):
        # Sense
        object_data = json.loads(msg.payload)
        largest_object = max(
            object_data,
            key=lambda object: object['w'] * object['h'],
            default=None)
        if largest_object:
            self.object_size = largest_object["w"]
            self.object_x = largest_object['x'] + (largest_object['w'] / 2)
        else:
            self.object_size = None

    def follow_object(self, client):
        speed_pid = PIDController(0.0003, 0.0007, smart_reset=True,
                                  windup_limit=120)
        direction_pid = PIDController(0.0003, 0.0007, smart_reset=True,
                                      windup_limit=120)
        # Look forward
        publish_json(client, "motors/servo/pan/position", 0)
        publish_json(client, "motors/servo/tilt/position", 0)
        time.sleep(0.1)
        publish_json(client, "motors/servo/pan/stop", None)
        publish_json(client, "motors/servo/tilt/stop", None)

        while True:
            # Think
            if self.object_size is None:
                # If no object detected, stop the robot
                publish_json(client, "motors/wheels", [0, 0])
                time.sleep(0.05)
                continue
            # Calculate errors
            direction_error = center_x - self.object_x
            speed_error = object_size_ref - self.object_size
            direction = direction_pid.control(direction_error)
            speed = speed_pid.control(speed_error)
            # Act
            publish_json(
                client,
                "object_follower/log",
                {
                    "direction_error": direction_error,
                    "speed_error": speed_error,
                    "direction": direction,
                    "speed": speed,
                },
            )
            publish_json(
                client, "motors/wheels", [speed - direction, speed + direction]
            )

            time.sleep(0.05)

    def start(self):
        client = connect()
        client.subscribe("colored_object_detector/detections")
        client.message_callback_add(
            "colored_object_detector/detections", self.on_object_detected
        )
        self.follow_object(client)


behavior = FollowObjectBehavior()
behavior.start()
