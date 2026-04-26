import os

import cv2
import torch
from torchvision import transforms, datasets
from torchvision.models.detection import ssdlite320_mobilenet_v3_large

from robot.common.camera_core import start, camera_app_url
from common.mqtt_behavior import connect, publish_json

torch.backends.quantized.engine = 'qnnpack'
GREEN = (0, 255, 0)
COCO_INSTANCE_CATEGORY_NAMES = datasets.CocoDetection.coco.CLASSES  # or hardcoded list

# W x H should be minimum of 224 - 320 x 240 should be enough

# About the model - https://pytorch.org/hub/pytorch_vision_mobilenet_v2/
# About the process - https://docs.pytorch.org/tutorials/intermediate/realtime_rpi.html
# https://gist.github.com/yrevar/942d3a0ac09ec9e5eb3a
# We want ssdlite320_mobilenet_v3_large
# https://docs.pytorch.org/vision/stable/models.html#table-of-all-available-object-detection-weights
# https://docs.pytorch.org/vision/0.12/models.html
# https://github.com/quic/aimet-model-zoo/blob/develop/aimet_zoo_torch/ssd_mobilenetv2/MobileNetV2-SSD-lite.md
# https://github.com/qfgaohao/pytorch-ssd/tree/master/vision/ssd
# https://github.com/pytorch/vision/blob/main/torchvision/models/detection/ssdlite.py
# https://docs.pytorch.org/vision/stable/models/ssdlite.html
# https://docs.pytorch.org/vision/stable/models.html#table-of-all-available-object-detection-weights

class ObjectDetector:
    def __init__(self):
        net = ssdlite320_mobilenet_v3_large(quantize=True)
        self.net = torch.jit.script(net)
        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            # For mobilenet v2/3
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        self.client = connect()

    def processor(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        input_tensor = self.preprocess(image)
        input_batch = input_tensor.unsqueeze(0)  # create a mini-batch as expected by the model
        with torch.no_grad(): # Makes it faster by not keeping track of gradients
            outputs = self.net(input_batch)
        ## Get the top 10





        objects = self.face_cascade.detectMultiScale(gray)
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), GREEN, 2)
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

# PyTorch torchaudio can do STT and TTS - speaking and listening.
# Speaking - https://docs.pytorch.org/audio/stable/tutorials/tacotron2_pipeline_tutorial.html
# Listening - https://docs.pytorch.org/audio/stable/index.html
# And has Pi 4 Inference.

