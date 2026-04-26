import os

import cv2

from robot.common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

cascade_path = "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml"

class FaceDetector:
    def __init__(self):
        assert os.path.exists(cascade_path), "Cascade file not found"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.client = connect()

    def processor(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        green = (0, 255, 0)
        objects = self.face_cascade.detectMultiScale(gray)
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), green, 2)
        if len(objects) > 0:
            publish_json(self.client, "object_detector/objects", [
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                for (x, y, w, h) in objects
            ])

        return frame

    def start(self):
        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=(320, 240))


if __name__ == "__main__":
    detector = FaceDetector()
    detector.start()
