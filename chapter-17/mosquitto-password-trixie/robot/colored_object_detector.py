import cv2


from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

SIZE = (704, 364)
GREEN = (0, 255, 0)


class ColoredObjectDetector:
    def __init__(self):
        self.low_range = (30, 90, 50)
        self.high_range = (80, 255, 255)
        self.client = connect()

    def processor(self, frame):
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        masked = cv2.inRange(frame_hsv, self.low_range, self.high_range)
        contours, _ = cv2.findContours(masked, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        rectangles = [cv2.boundingRect(cnt) for cnt in contours]
        [cv2.rectangle(frame, (x, y), (x + w, y + h), GREEN)
            for x, y, w, h in rectangles]

        publish_json(
            self.client,
            "colored_object_detector/detections",
            [
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}
                for x, y, w, h in rectangles
            ],
        )

        return frame

    def start(self):
        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = ColoredObjectDetector()
    detector.start()
