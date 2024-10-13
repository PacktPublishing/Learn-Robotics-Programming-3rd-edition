import atexit
import time
import vl53l5cx_ctypes
from common.mqtt_behavior import connect, publish_json

VALID_STATUSES = (vl53l5cx_ctypes.STATUS_RANGE_VALID, vl53l5cx_ctypes.STATUS_RANGE_VALID_LARGE_PULSE)
class DistanceSensorService:
    def __init__(self):
        self.sensor = vl53l5cx_ctypes.VL53L5CX()
        self.sensor.set_resolution(8 * 8)
        self.sensor.set_ranging_frequency_hz(10)

    def start_ranging(self, *args):
        self.sensor.start_ranging()

    def stop_ranging(self, *args):
        self.sensor.stop_ranging()

    def update_data(self):
        data = self.sensor.get_data()
        as_list = list(data.distance_mm[0])
        # Skip low confidence data
        for n, data in enumerate(list(data.target_status[0])):
            if data not in VALID_STATUSES:
                as_list[n] = 3000 # max 3m.
        publish_json(self.client, "sensors/distance_mm", as_list)

    def loop_forever(self):
        print("Making connection")
        self.client = connect()
        self.client.subscribe("sensors/distance/control/#")
        self.client.message_callback_add("sensors/distance/control/start_ranging", self.start_ranging)
        self.client.message_callback_add("sensors/distance/control/stop_ranging", self.stop_ranging)
        self.client.publish("sensors/distance/status", "ready")
        self.client.message_callback_add("all/stop", self.stop_ranging)
        print("Starting loop")
        while True:
            if self.sensor.data_ready():
                self.update_data()
            time.sleep(0.01)

print("Initialising sensor")
service = DistanceSensorService()
atexit.register(service.stop_ranging)
service.loop_forever()
