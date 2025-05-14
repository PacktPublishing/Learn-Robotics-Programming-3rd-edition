# https://docs.opencv.org/4.x/d4/d2f/tf_det_tutorial_dnn_conversion.html
# https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html

# https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
# We will be using OpenCV fast face detection, based on the DNN module

import os

import cv2

from common.image_app_core import start, camera_app_location
from common.mqtt_behavior import connect, publish_json


MODEL_FILE = "face_detection_yunet_2023mar_int8.onnx"
SIZE = (640, 480)
SCORE_THRESHOLD = 0.7 # Filter faces scoring less than this
NMS_THRESHOLD = 0.3 # Suppress bounding boxes of iou >= nms_threshold
TOP_K = 5000 # Max number of boxes before NMS
# What is nms?
# Non-Maximum Suppression (NMS) is a technique used in object detection to eliminate redundant bounding boxes around the same object.

# It works by selecting the bounding box with the highest confidence score and removing all other boxes that have a high overlap (Intersection over Union, IoU) with it.
# This process is repeated until no more boxes remain that have a high overlap with the selected boxes.

# TOP_K 0 number of boxes to keep before NMS
GREEN = (0, 255, 0)

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
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = self.detector.detect(frame)
        if faces[1] is not None:
            # print(f"Detected {len(faces[1])} faces")
            # print(f"Detected {repr(faces[1])}")
            detected = [(int(face[0]), int(face[1]),
                         int(face[2]), int(face[3]), face[-1]) for face in faces[1]]
            # print(f"Extracted `{repr(detected)}`")
            for x, y, w, h, score in detected:
                # print(f"Making a rectangle for x: {x}, y: {y}, w: {w}, h: {h}, score: {score}")
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
        self.client.subscribe("camera_view/location/get")
        self.client.message_callback_add("camera_view/location/get", camera_app_location)
        camera_app_location(self.client, None, None)
        start(self.processor, size=SIZE)


if __name__ == "__main__":
    detector = FaceDetector()
    detector.start()
