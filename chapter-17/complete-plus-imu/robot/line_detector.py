import cv2
import numpy as np

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

SIZE = (704, 364)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
MIDDLE = 320 / 2

class LineDetector:
    def __init__(self):
        self.client = connect()

    def find_line(self, resized):
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        masked = cv2.inRange(gray, 0, 50)
        contours, _ = cv2.findContours(masked, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(resized, [largest_contour], -1, GREEN, 2)
        rect = cv2.minAreaRect(largest_contour)
        ((center_x, center_y)), (width, height), theta = rect
        if min(width, height) < 10:
            return None

        if width < height:
            theta += 90.0
            length = height
        else:
            length = width

        theta = (-theta) % 180

        theta = np.deg2rad(theta)
        end = (
            int(center_x + length/2 * np.cos(theta)),
            int(center_y - length/2 * np.sin(theta))
        )
        cv2.line(resized, (int(center_x), int(center_y)), end, RED, 2)
        return end[0] - MIDDLE

    def processor(self, frame):
        resized = cv2.resize(frame, (320, 240))
        position = self.find_line(resized)

        publish_json(
            self.client,
            "line_detector/position",
            {"line": position},
        )

        return resized

    def start(self):
        # Look down
        publish_json(self.client, "motors/servo/pan/position", 0)
        publish_json(self.client, "motors/servo/tilt/position", 80)

        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = LineDetector()
    detector.start()
