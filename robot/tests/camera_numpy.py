import time
from picamera2 import Picamera2

with Picamera2() as camera:
    camera.start()
    while True:
        time.sleep(0.1)
        array = camera.capture_array("main")
        print(array.shape)
