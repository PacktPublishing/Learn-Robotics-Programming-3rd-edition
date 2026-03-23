import time
import json

from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController

pan_range = 70
tilt_range = 50
class LookAtFaceBehavior:
    center_x = 320
    center_y = 240

    def __init__(self):
        self.face_x = self.center_x
        self.face_y = self.center_y

    def look_at_face(self, client):
        self.tilt_pid = PIDController(0, 0.01)
        self.pan_pid = PIDController(0, 0.01)
        while True:
            # Think
            pan_error = self.center_x - self.face_x
            tilt_error = self.center_y - self.face_y

            pan_position = max(-pan_range, min(pan_range, self.pan_pid.control(pan_error)))
            tilt_position = max(-tilt_range, min(tilt_range, self.tilt_pid.control(tilt_error)))
            print("Pan position:", pan_position)
            print("Tilt position:", tilt_position)

            # Act
            publish_json(client, "motors/servo/pan/position", pan_position)
            publish_json(client, "motors/servo/tilt/position", -tilt_position) # Inverted tilt
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
            self.face_x = self.center_x
            self.face_y = self.center_y

    def start(self):
        client = connect()
        client.subscribe("face_detector/faces")
        client.message_callback_add("face_detector/faces", self.on_faces_detected)
        self.look_at_face(client)


behavior = LookAtFaceBehavior()
behavior.start()
