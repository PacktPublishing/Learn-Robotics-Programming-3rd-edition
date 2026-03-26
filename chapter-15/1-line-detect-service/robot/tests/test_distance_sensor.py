import atexit
import time
import vl53l5cx_ctypes

print("Initializing distance sensor...")
sensor = vl53l5cx_ctypes.VL53L5CX()
print("Setting distance sensor resolution and frequency")
sensor.set_resolution(8 * 8)
sensor.set_ranging_frequency_hz(10)
print("Starting distance sensor ranging")
sensor.start_ranging()
atexit.register(sensor.stop_ranging)

while True:
    if sensor.data_ready():
        data = sensor.get_data()
        print(data.distance_mm[0][7], data.distance_mm[0][0])
    time.sleep(0.01)
