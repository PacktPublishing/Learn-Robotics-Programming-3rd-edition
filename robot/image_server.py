import time

from flask import Flask, Response

import common.camera_stream as camera_stream

app = Flask(__name__)
camera = camera_stream.setup_camera()

def frame_generator():
    time.sleep(0.1)
    for frame in camera_stream.start_stream(camera):
        encoded_bytes = camera_stream.encode_frame(frame)
        yield (b'--frame\r\n' + 
            b'Content-Type: image/jpeg\r\n\r\n' + encoded_bytes + b'\r\n')

@app.route("/")
def stream():
    response = Response(frame_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5014) # use chapter number in ports that aren't the main server
