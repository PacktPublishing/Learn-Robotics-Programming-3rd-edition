import json
import time

from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055

from common.mqtt_behavior import connect, publish_json

client = connect()
i2c = I2C(2)
bno055 = adafruit_bno055.BNO055_I2C(i2c)

while True:
    status = bno055.calibration_status
    publish_json(client, "sensors/imu/status", {
        "sys": status[0],
        "gyro": status[1],
        "acc": status[2],
        "mag": status[3],
    })
    gyro = bno055.gyro
    publish_json(client, "sensors/imu/gyro", {
        "x": gyro[0],
        "y": gyro[1],
        "z": gyro[2],
    })
    acc = bno055.acceleration
    publish_json(client, "sensors/imu/accelerometer", {
        "x": acc[0],
        "y": acc[1],
        "z": acc[2],
    })
    magnetometer = bno055.magnetic
    publish_json(client, "sensors/imu/magnetometer", {
        "x": magnetometer[0],
        "y": magnetometer[1],
        "z": magnetometer[2],
    })
    euler = bno055.euler
    publish_json(client, "sensors/imu/euler", {
        "heading": euler[0],
        "roll": euler[1],
        "pitch": euler[2],
    })

    time.sleep(0.1)
