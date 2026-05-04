import time
import math
from common.mqtt_behavior import connect, publish_json


class CircleHeadBehavior:
    def __init__(self):
        self.seconds_per_circle = 10
        self.radians_per_second = (2 * math.pi) / self.seconds_per_circle
        self.radius = 50

    def start(self):
        client = connect(start_loop=False)
        client.loop_start()
        while True:
            frame_in_radians = time.monotonic() * self.radians_per_second
            pan_position = self.radius * math.sin(frame_in_radians)
            tilt_position = self.radius * math.cos(frame_in_radians)
            publish_json(client, "motors/servo/pan/position", pan_position)
            publish_json(client, "motors/servo/tilt/position", tilt_position)
            time.sleep(0.05)


behavior = CircleHeadBehavior()
behavior.start()
