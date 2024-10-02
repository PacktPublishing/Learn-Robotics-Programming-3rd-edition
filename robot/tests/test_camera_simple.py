from picamera2 import Picamera2
picam2 = Picamera2()
config = picam2.create_still_configuration()
if config is None:
    exit("create_still_configuration failed")
picam2.configure(config)
picam2.start()
picam2.capture_file("test.jpg")
