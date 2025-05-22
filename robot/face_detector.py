# https://docs.opencv.org/4.x/d4/d2f/tf_det_tutorial_dnn_conversion.html
# https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html

# We will be using OpenCV fast face detection, based on the DNN module
# https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html
# https://docs.opencv.org/4.x/da/d9d/tutorial_dnn_yolo.html - for something interesting?
import os

import cv2

from common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json


SIZE = (640, 480)
GREEN = (0, 255, 0)
MODEL_FILE = "face_detection_yunet_2023mar_int8.onnx"
SCORE_THRESHOLD = 0.7 # Filter faces scoring less than this
# NMS_THRESHOLD = 0.3 # Suppress bounding boxes of iou >= nms_threshold
# TOP_K = 5000 # Max number of boxes before NMS
# # What is nms?
# # Non-Maximum Suppression (NMS) is a technique used in object detection to eliminate redundant bounding boxes around the same object.

# # It works by selecting the bounding box with the highest confidence score and removing all other boxes that have a high overlap (Intersection over Union, IoU) with it.
# # This process is repeated until no more boxes remain that have a high overlap with the selected boxes.

# # TOP_K 0 number of boxes to keep before NMS

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
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h), "score": float(score)}
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
