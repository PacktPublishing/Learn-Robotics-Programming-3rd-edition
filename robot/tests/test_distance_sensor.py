import vl53l5cx_ctypes
import time

sensor = vl53l5cx_ctypes.VL53L5CX()
sensor.set_resolution(8 * 8)
sensor.set_ranging_frequency_hz(15)
sensor.start_ranging()
while True:
    if sensor.data_ready():
        data = sensor.get_data()
        print(data.distance_mm[0][0], data.distance_mm[0][7])
    time.sleep(0.01)
