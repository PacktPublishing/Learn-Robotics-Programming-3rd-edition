import os

import cv2

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

SIZE = (704, 364)
GREEN = (0, 255, 0)
MODEL_FILE = "face_detection_yunet_2023mar_int8.onnx"
SCORE_THRESHOLD = 0.7


class FaceDetector:
    def __init__(self):
        assert os.path.exists(MODEL_FILE), "Model file not found"
        self.detector = cv2.FaceDetectorYN.create(
            MODEL_FILE,
            "",
            SIZE,
            SCORE_THRESHOLD,
        )

        self.client = connect()

    def processor(self, frame):
        _, faces = self.detector.detect(frame)
        if faces is not None:
            detected = [(int(face[0]), int(face[1]),
                        int(face[2]), int(face[3]), face[-1]) for face in faces]
            for x, y, w, h, score in detected:
                cv2.rectangle(frame, (x, y), (x + w, y + h), GREEN, 1)
                cv2.putText(frame, f"{score:.2f}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 2)

            publish_json(self.client, "face_detector/faces", [
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h),
                "score": float(score)}
                for (x, y, w, h, score) in detected
            ])
        else:
            publish_json(self.client, "face_detector/faces", [])

        return frame

    def start(self):
        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        camera_app_url(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = FaceDetector()
    detector.start()
