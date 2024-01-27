import ujson as json
import vl53l5cx_ctypes
import numpy as np
import time

from mqtt_behavior import connect


class DistanceSensorService:
    def __init__(self) -> None:
        sensor = vl53l5cx_ctypes.VL53L5CX()
        self.resolution = 8 * 8
        sensor.set_resolution(self.resolution)
        sensor.set_ranging_frequency_hz(10)
        self.sensor = sensor
        self.is_ranging = False

    def start_ranging(self, client, userdata, msg):
        self.sensor.start_ranging()
        self.is_ranging = True

    def stop_ranging(self, client, userdata, msg):
        self.sensor.stop_ranging()
        self.is_ranging = False

    def set_resolution(self, client, userdata, msg):
        self.resolution = int(msg.payload.decode("utf-8"))
        self.sensor.set_resolution(self.resolution)

    def update_data(self):
        data = self.sensor.get_data()
        # # Skip low confidence data
        # if any(status not in (5, 9) for status in data.target_status):
        #     print("Skipping low confidence data:", data.target_status)
        #     return
        as_array = np.array(data.distance_mm)
        if self.resolution == 64:
            as_array = as_array.reshape((8, 8))
        elif self.resolution == 16:
            as_array = as_array[0][:16].reshape((4, 4))
        flipped = np.flipud(as_array)
        as_json = json.dumps(flipped.tolist())
        self.client.publish("sensors/distance_mm", as_json)

    def loop_forever(self):
        print("Making connection")
        client = connect()
        client.subscribe("sensors/distance/control/#")
        client.message_callback_add("sensors/distance/control/start_ranging", self.start_ranging)
        client.message_callback_add("sensors/distance/control/stop_ranging", self.stop_ranging)
        client.message_callback_add("sensors/distance/control/set_resolution", self.set_resolution)
        client.publish("sensors/distance/status", "ready")
        self.client = client
        print("Starting loop")
        while True:
            if self.is_ranging and self.sensor.data_ready():
                self.update_data()
            time.sleep(0.01)

print("Initialising sensor")
service = DistanceSensorService()
print("Sensor ready, starting loop")
service.loop_forever()
