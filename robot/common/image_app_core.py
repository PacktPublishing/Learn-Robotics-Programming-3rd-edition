import time
from multiprocessing import Process, Queue

from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np

app = Flask(__name__)
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
frame_buffer = Queue(maxsize=2)


def buffer_frame(frame):
    if frame_buffer.empty():
        frame_buffer.put(frame)


def encode_frame(frame):
    _, jpeg = cv2.imencode(".jpg", frame, encode_param)
    return jpeg.tobytes()


def frame_generator():
    while True:
        time.sleep(0.05)
        frame = frame_buffer.get()
        bytes = encode_frame(frame)
        yield (b'--frame\r\n' +
               b'Content-Type: image/jpeg\r\n\r\n' + bytes + b'\r\n')


@app.route("/")
def stream():
    response = Response(
        frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def start_server_process():
    server = Process(target=app.run, kwargs={
        "host": "0.0.0.0",
        "port": 5001})
    server.start()
    return server


def start(processor, size=(320, 240)):
    camera = Picamera2()
    config = camera.create_video_configuration(
            main={"format": 'XRGB8888', "size": size}
        )

    camera.configure(config)
    camera.start()

    server = start_server_process()
    try:
        while True:
            frame = camera.capture_array("main")
            buffer_frame(processor(frame))
    finally:
        server.terminate()
        server.join()
