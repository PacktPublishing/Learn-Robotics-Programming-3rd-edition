from time import sleep
from common.mqtt_behavior import connect, publish_json
import numpy as np
import ujson as json


class ProportionalObstacleAvoidingBehavior:
    def __init__(self):
        self.speed = 0.6
        self.curve_proportion = 140
        # Lower proportion = smoother, but more likely to steer into something.
        # Higher proportion, corrects away from a collision, but will have a characteristic proportional wobble.
        # TODO: Pause behavior with setting?

    def behavior_settings(self, client, userdata, msg):
        try:
            settings = json.loads(msg.payload)
            if "speed" in settings:
                self.speed = settings["speed"]
            if "curve_proportion" in settings:
                self.curve_proportion = settings["curve_proportion"]
            print(f"Updated settings: {settings}")
        except Exception as e:
            print(f"Failed to update settings: {e}, {msg.payload}")
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("sensors/distance_mm")
        client.message_callback_add("sensors/distance_mm", self.data_received)
        client.subscribe("behavior/settings")
        client.message_callback_add("behavior/settings", self.behavior_settings)
        client.publish("sensors/distance/control", "start_ranging")

    def data_received(self, client, userdata, msg):
        # Sense
        sensor_data = json.loads(msg.payload)
        as_array = np.array(sensor_data)
        top_lines = as_array[:4, :]
        left_sensors = top_lines[:, :2]
        right_sensors = top_lines[:, -2:]
        left_distance = int(np.min(left_sensors))
        right_distance = int(np.min(right_sensors))
        # Think
        nearest_distance = min(left_distance, right_distance)
        inverse = 1/max(nearest_distance, 1)
        curve = self.curve_proportion * inverse
        furthest_speed = np.clip(self.speed - curve, -1, 1)
        nearest_speed = np.clip(self.speed + curve, -1, 1)

        if left_distance < right_distance:
            left_motor_speed = nearest_speed
            right_motor_speed = furthest_speed
        else:
            left_motor_speed = furthest_speed
            right_motor_speed = nearest_speed

        # Act
        log_data = {
            "left_distance": left_distance, 
            "right_distance": right_distance, 
            "left_motor_speed": left_motor_speed, 
            "right_motor_speed": right_motor_speed
        }
        publish_json(client, "log/obstacle_avoider", log_data)
        print(log_data)
        publish_json(client, "motors/wheels", [left_motor_speed, right_motor_speed])

    def run(self):
        self.client = connect(self.on_connect, start_loop=False)
        self.client.loop_forever()

behavior = ProportionalObstacleAvoidingBehavior()
behavior.run()
