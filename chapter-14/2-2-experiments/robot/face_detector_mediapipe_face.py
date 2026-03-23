import pathlib

import cv2
import mediapipe as mp


from robot.common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
FaceDetectorResult = mp.tasks.vision.FaceDetectorResult
VisionRunningMode = mp.tasks.vision.RunningMode

MODEL_PATH = pathlib.Path("~/face_detection_short_range.tflite").expanduser()
GREEN = (0, 255, 0)

# About the process - https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/python

# About the model - https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector/index#blazeface_short-range
# https://arxiv.org/abs/1512.02325

class ObjectDetector:
    def __init__(self):
        assert MODEL_PATH.exists(), f"Model not found at {MODEL_PATH}"
        self.mp_options = FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=VisionRunningMode.IMAGE)
        self.client = None
        self.detector = None

    def processor(self, frame):
        # Prepare
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        # Detect
        result = self.detector.detect(mp_image)
        # Handle the results
        for detections in result.detections:
            for location in detections.bounding_box:
                x = int(location.origin_x)
                y = int(location.origin_y)
                w = int(location.width)
                h = int(location.height)
                cv2.rectangle(frame,
                    (x, y),
                    (x + w, y + h),
                    GREEN, 2)
        # Publish the results
        if len(result.detections) > 0:
            publish_json(self.client, "object_detector/faces", [
                {"x": int(location.origin_x), "y": int(location.origin_y),
                 "w": int(location.width), "h": int(location.height)}
                for detections in result.detections
                for location in detections.bounding_box
            ])

        return frame

    def start(self):
        self.client = connect()
        self.client.subscribe("camera_view/url/get")
        self.client.message_callback_add("camera_view/url/get", camera_app_url)
        with FaceDetector.create_from_options(self.mp_options) as detector:
            self.detector = detector
            camera_app_url(self.client, None, None)
            start(self.processor, size=(320, 240))

if __name__ == "__main__":
    detector = FaceDetector()
    detector.start()


# MediaPipe - does not offer Speach to text/text to speach pipelines
# Nor does tflite/litert.

