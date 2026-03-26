from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055
import time

i2c = I2C(2)
bno055 = adafruit_bno055.BNO055_I2C(i2c)

while True:
    print("Acc Calibration:", bno055.calibration_status[2], "Acc:", bno055.acceleration)
    time.sleep(0.1)
