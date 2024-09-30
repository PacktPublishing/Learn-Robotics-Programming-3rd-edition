import board
import adafruit_bno055
import time

i2c = board.I2C()
bno055 = adafruit_bno055.BNO055_I2C(i2c)

while True:
    print(bno055.euler)
    time.sleep(0.1)
