from picamera2 import Picamera2
import cv2
import numpy as np

size = (320, 240)
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

def setup_camera():
    camera = Picamera2()
    camera.configure(camera.create_video_configuration(main={"size": size}))
    return camera

def start_stream(camera):
    camera.start()
    while True:
        frame = camera.capture_array("main")
        print(frame.shape)
        frame = np.flip(frame, 0)
        yield frame

def encode_frame(frame):
    _, jpeg = cv2.imencode(".jpg", frame, encode_param)
    return jpeg.tobytes()
