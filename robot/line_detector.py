import cv2
import numpy as np

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

SIZE = (704, 364)
GREEN = (0, 255, 0)
RED = (0, 0, 255)


class LineDetector:
    def __init__(self):
        self.row_number = 180
        self.client = connect()

    def processor(self, frame):
        resized = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        blurred = cv2.blur(gray, (10, 10), 0)
        row = blurred[self.row_number].astype(np.int32)
        diff = np.diff(row)

        max_d = np.amax(diff)
        min_d = np.amin(diff)
        highest = np.where(diff == max_d)[0][0]
        lowest = np.where(diff == min_d)[0][0]

        cv2.line(resized, (0, self.row_number), (320, self.row_number), GREEN, 2)

        if max_d < 5 or min_d > -5:
            publish_json(
                self.client,
                "line_detector/position",
                {"line": None},
            )
            return resized

        middle = (highest + lowest) / 2

        publish_json(
            self.client,
            "line_detector/position",
            {"line": middle},
        )

        cv2.line(resized, (int(middle), 0), (int(middle), 240), RED, 2)
        return resized

    def start(self):
        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = LineDetector()
    detector.start()
