"""
Test the VL53L5CX distance sensor in 4x4 resolution mode.
Useful for lower bandwidth / faster update scenarios.
"""
import time
import numpy as np
import vl53l5cx_ctypes

sensor = vl53l5cx_ctypes.VL53L5CX()
sensor.set_resolution(4 * 4)
sensor.set_ranging_frequency_hz(10)
sensor.start_ranging()

while True:
    if sensor.data_ready():
        as_array = np.array(sensor.get_data().distance_mm)[0][:16]
        as_grid = as_array.reshape((4, 4))
        as_grid = np.flipud(as_grid)
        print(as_grid)
    time.sleep(0.1)
