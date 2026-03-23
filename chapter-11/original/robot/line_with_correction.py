from common.mqtt_behavior import connect, publish_json
from common.pid_control import PIController
import numpy as np
import ujson as json


class LineWithCorrectionBehavior:
    def __init__(self):
        self.speed = 0.6
        self.running = False
        self.veer_controller = PIController(0.2, 0.3)
        # Lower proportion = smoother, but more likely to steer into something.
        # Higher proportion, corrects away from a collision, but will have a characteristic proportional wobble.

    def behavior_settings(self, client, userdata, msg):
        try:
            settings = json.loads(msg.payload)
            if "speed" in settings:
                self.speed = settings["speed"]
            if "running" in settings:
                self.running = settings["running"]
            if "veer_proportion" in settings:
                self.veer_controller.k_p = settings["veer_proportion"]
            if "veer_integral" in settings:
                self.veer_controller.k_i = settings["veer_integral"]
            print(f"Updated settings: {settings}")
        except Exception as e:
            print(f"Failed to update settings: {e}, {msg.payload}")

    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/encoders/data")
        client.message_callback_add("sensors/encoders/data", self.data_received)
        client.subscribe("behavior/settings")
        client.message_callback_add("behavior/settings", self.behavior_settings)

        publish_json(
            client, "sensors/encoders/control", 
            {"running": True, "frequency": 10, "reset": True}
        )

    def data_received(self, client, userdata, msg):
        if self.running:
            # Sense
            sensor_data = json.loads(msg.payload)
            # Think
            left = sensor_data["left_delta"]
            right = sensor_data["right_delta"]
            error = right - left
            veer = self.veer_controller.control(error, sensor_data["delta_time"])
            left_motor_speed = np.clip(self.speed + veer, -1, 1)
            right_motor_speed = np.clip(self.speed - veer, -1, 1)
            # Act
            log_data = {
                "left": left,
                "right": right,
                "left_motor_speed": left_motor_speed,
                "right_motor_speed": right_motor_speed,
                "veer": veer,
                "error": error,
            }
            publish_json(client, "behavior/log", log_data)
            publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])
        else:
            publish_json(client, "motors/wheels", [0, 0])

    def run(self):
        self.client = connect(self.on_connect, start_loop=False)
        self.client.loop_forever()

behavior = LineWithCorrectionBehavior()
behavior.run()
