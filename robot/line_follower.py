import time
import json

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController

speed = 0.4

class FollowLineBehavior:
    def __init__(self):
        self.line_error = 0

    def on_line_detected(self, client, userdata, msg):
        # Sense
        data = json.loads(msg.payload)
        self.line_error = data["line"]

    def follow_line(self, client):
        line_pid = PIDController(0.001, 0.0001, 0.001,
                                 smart_reset=True)
        turn = 0
        while True:
            # Think
            if self.line_error is None:
                # If no line is detected, continue the last turn
                # but reset the PID
                line_pid.reset()
                print("No line")
                # return
            else:
                # Calculate errors
                turn = -line_pid.control(self.line_error)
                left = speed - turn
                right = speed + turn

                # Act
                publish_json(
                    client,
                    "line_follower/log",
                    {
                        "direction_error": self.line_error / 100,
                        "turn": turn,
                        "time": time.time()
                    },
                )
            publish_json(
                client, "motors/wheels", [left, right]
            )

            time.sleep(0.05)

    def start(self):
        client = connect()
        client.subscribe("line_detector/position")
        client.message_callback_add(
            "line_detector/position", self.on_line_detected
        )
        self.follow_line(client)


behavior = FollowLineBehavior()
behavior.start()
