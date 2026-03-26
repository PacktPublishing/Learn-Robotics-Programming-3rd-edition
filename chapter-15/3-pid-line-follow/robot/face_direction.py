import atexit
import time
import ujson as json

import numpy as np
from common.mqtt_behavior import connect, publish_json
from common.pid_controller import PIDController
from common.time_stepper import TimeStepper

class FaceDirectionBehavior:
    def __init__(self):
        self.pid = PIDController(0.4, 0.2, smart_reset=True)
        self.time_stepper = TimeStepper()
        self.target_yaw = 0

    def on_imu_data(self, client, userdata, message):
        # Sense
        imu_data = json.loads(message.payload)
        current_yaw = imu_data['yaw']
        time_difference = self.time_stepper.step()

        # Think
        yaw_error = self.target_yaw - current_yaw
        if yaw_error > np.pi:
            yaw_error -= 2 * np.pi
        if yaw_error < -np.pi:
            yaw_error += 2 * np.pi
        control_signal = self.pid.control(yaw_error, time_difference)
        # Act
        publish_json(client, "face_direction/plot", {
            "yaw_error": yaw_error,
            "control_signal": control_signal,
            "time": time.time()
        })
        publish_json(client, "motors/wheels", [control_signal, -control_signal])

    def stop(self, client):
        print("Stopping motors")
        publish_json(client, "motors/wheels", [0, 0])
        client.publish("launcher/stop", "imu_service")

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("sensors/imu/euler")
        client.message_callback_add("sensors/imu/euler", self.on_imu_data)
        client.publish("launcher/start", "imu_service")
        atexit.register(self.stop, client)
        client.loop_forever()

behavior = FaceDirectionBehavior()
behavior.start()
