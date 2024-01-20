import json
import vl53l5cx_ctypes
import numpy as np
import time

from mqtt_behavior import connect


class DistanceSensorService:
    def __init__(self) -> None:
        sensor = vl53l5cx_ctypes.VL53L5CX()
        sensor.set_resolution(8 * 8)
        sensor.set_ranging_frequency_hz(10)
        self.sensor = sensor
        self.is_ranging = False

    def start_ranging(self, client, userdata, msg):
        self.sensor.start_ranging()
        self.is_ranging = True

    def stop_ranging(self, client, userdata, msg):
        self.sensor.stop_ranging()
        self.is_ranging = False

    def update_data(self):
        data = self.sensor.get_data()
        as_array = np.array(data.distance_mm).reshape((8, 8))
        flipped = np.flipud(as_array)
        as_json = json.dumps(flipped.tolist())
        self.client.publish("sensors/distance_mm", as_json)

    def loop_forever(self):
        print("Making connection")
        client = connect()
        client.subscribe("sensors/distance/control/#")
        client.message_callback_add("sensors/distance/control/start_ranging", self.start_ranging)
        client.message_callback_add("sensors/distance/control/stop_ranging", self.stop_ranging)
        client.publish("sensors/distance/status", "ready")
        self.client = client
        client.loop_start()
        print("Starting loop")
        while True:
            if self.is_ranging and self.sensor.data_ready():
                self.update_data()
            time.sleep(0.01)

print("Initialising sensor")
service = DistanceSensorService()
print("Sensor ready, starting loop")
service.loop_forever()
