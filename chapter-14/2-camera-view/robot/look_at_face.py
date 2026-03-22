import time
import json

import numpy as np

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController



pan_range = 70
tilt_range = 50
center_x = 320
center_y = 240

class LookAtFaceBehavior:
    def __init__(self):
        self.face_x = center_x
        self.face_y = center_y

    def look_at_face(self, client):
        self.pan_pid = PIDController(0, 0.006)
        self.tilt_pid = PIDController(0, -0.006)  # Inverted tilt
        while True:
            # Think
            pan_error = center_x - self.face_x
            tilt_error = center_y - self.face_y
            pan_position = self.pan_pid.control(pan_error)
            tilt_position = self.tilt_pid.control(tilt_error)
            pan_position = np.clip(pan_position, -pan_range, pan_range)
            tilt_position = np.clip(tilt_position, -tilt_range, tilt_range)
            # Act
            publish_json(client, "motors/servo/pan/position", pan_position)
            publish_json(client, "motors/servo/tilt/position", tilt_position)
            time.sleep(0.05)

    def on_faces_detected(self, client, userdata, msg):
        # Sense
        face_data = json.loads(msg.payload)
        largest_face = max(face_data, key=lambda face: face['w'] * face['h'], default=None)
        # Only update face_x and face_y if a face is detected
        if largest_face:
            self.face_x = largest_face['x'] + (largest_face['w'] / 2)
            self.face_y = largest_face['y'] + (largest_face['h'] / 2)
            print("Largest face detected at:", self.face_x, self.face_y)
        else:
            # If no face is detected, reset the face coordinates to the center
            self.face_x = center_x
            self.face_y = center_y

    def start(self):
        client = connect()
        client.subscribe("face_detector/faces")
        client.message_callback_add("face_detector/faces", self.on_faces_detected)
        self.look_at_face(client)


behavior = LookAtFaceBehavior()
behavior.start()
