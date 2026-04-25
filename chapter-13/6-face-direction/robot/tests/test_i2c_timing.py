"""
Diagnostic: measure I2C read times for BNO055 and VL53L5CX together.
Useful when investigating bus contention or slow read issues.
Run with: robotpython tests/test_i2c_timing.py
"""
import time

import adafruit_bno055
import vl53l5cx_ctypes
from adafruit_extended_bus import ExtendedI2C as I2C

from common.i2c_timing import i2c_profile, summarise_i2c_timings

i2c = I2C(2)
bno055 = adafruit_bno055.BNO055_I2C(i2c)

sensor = vl53l5cx_ctypes.VL53L5CX()
sensor.set_resolution(8 * 8)
sensor.set_ranging_frequency_hz(15)
sensor.start_ranging()


@i2c_profile
def read_bno055():
    return bno055.euler


@i2c_profile
def read_distance():
    if sensor.data_ready():
        return sensor.get_data()
    return None


print("Running I2C timing test for 5 seconds...")
end_time = time.monotonic() + 5.0
while time.monotonic() < end_time:
    euler = read_bno055()
    distance = read_distance()
    print(f"Euler: {euler}  Distance[0,0]: {distance.distance_mm[0][0] if distance else 'N/A'}")
    time.sleep(0.05)

summarise_i2c_timings()
