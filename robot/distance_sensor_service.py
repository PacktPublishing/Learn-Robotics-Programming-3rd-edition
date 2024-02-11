import time
import ujson as json
import vl53l5cx_ctypes
import numpy as np

from common.mqtt_behavior import connect


class DistanceSensorService:
    def __init__(self) -> None:
        self.sensor = vl53l5cx_ctypes.VL53L5CX()
        self.sensor.set_resolution(8 * 8)
        self.sensor.set_ranging_frequency_hz(10)
        self.is_ranging = False

    def start_ranging(self, client, userdata, msg):
        self.sensor.start_ranging()
        self.is_ranging = True

    def stop_ranging(self, client, userdata, msg):
        self.sensor.stop_ranging()
        self.is_ranging = False

    def update_data(self):
        data = self.sensor.get_data()
        as_array = np.array(data.distance_mm[0])
        # Skip low confidence data
        for n, data in enumerate(np.array(data.target_status[0])):
            if data not in (vl53l5cx_ctypes.STATUS_RANGE_VALID, vl53l5cx_ctypes.STATUS_RANGE_VALID_LARGE_PULSE):
                as_array[n] = 3000 # max 3m.
        flipped = np.flip(as_array).reshape((8, 8))
        as_json = json.dumps(flipped.tolist())
        self.client.publish("sensors/distance_mm", as_json)

    def loop_forever(self):
        print("Making connection")
        self.client = connect()
        self.client.subscribe("sensors/distance/control/#")
        self.client.subscribe("all/stop")
        self.client.message_callback_add("sensors/distance/control/start_ranging", self.start_ranging)
        self.client.message_callback_add("sensors/distance/control/stop_ranging", self.stop_ranging)
        self.client.message_callback_add("all/stop", self.stop_ranging)
        self.client.publish("sensors/distance/status", "ready")
        print("Starting loop")
        while True:
            if self.is_ranging and self.sensor.data_ready():
                self.update_data()
            time.sleep(0.01)

print("Initialising sensor")
service = DistanceSensorService()
print("Sensor ready, starting loop")
service.loop_forever()
