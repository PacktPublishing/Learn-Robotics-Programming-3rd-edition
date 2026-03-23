import json
import time
import numpy as np

from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055

from common.mqtt_behavior import connect, publish_json

client = connect(start_loop=False)
i2c = I2C(2)
bno055 = adafruit_bno055.BNO055_I2C(i2c)

def store_calibration():
    bno055.mode = adafruit_bno055.CONFIG_MODE
    try:
        calibration = {
            'offsets_accelerometer': bno055.offsets_accelerometer,
            'offsets_magnetometer': bno055.offsets_magnetometer,
            'offsets_gyroscope': bno055.offsets_gyroscope,
            'radius_accelerometer': bno055.radius_accelerometer,
            'radius_magnetometer': bno055.radius_magnetometer,
        }
    finally:
        bno055.mode = adafruit_bno055.NDOF_MODE
    publish_json(client, "config/set",
                 ["imu/calibration", json.dumps(calibration)]
                 )

def calibration_received(calibration_data):
    # We are already calibrated
    if bno055.calibration_status[0] == 3:
        return
    unpacked = json.loads(calibration_data)
    bno055.mode = adafruit_bno055.CONFIG_MODE
    try:
        bno055.offsets_accelerometer = tuple(unpacked['offsets_accelerometer'])
        bno055.offsets_magnetometer = tuple(unpacked['offsets_magnetometer'])
        bno055.offsets_gyroscope = tuple(unpacked['offsets_gyroscope'])
        bno055.radius_accelerometer = unpacked['radius_accelerometer']
        bno055.radius_magnetometer = unpacked['radius_magnetometer']
    finally:
        bno055.mode = adafruit_bno055.NDOF_MODE

def on_config_updated(client, userdata, message):
    data = json.loads(message.payload)
    if 'imu/calibration' in data:
        calibration_received(data['imu/calibration'])

client.subscribe("config/updated")
client.message_callback_add("config/updated", on_config_updated)
publish_json(client, "config/get", ["imu/calibration"])

previous_status = (0, 0, 0, 0)

while True:
    status = bno055.calibration_status
    publish_json(client, "sensors/imu/status", {
        "sys": status[0],
        "gyro": status[1],
        "acc": status[2],
        "mag": status[3],
    })
    if tuple(status) != previous_status:
        previous_status = tuple(status)
        if all(item == 3 for item in status):
            store_calibration()

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
    euler = np.radians(bno055.euler)
    publish_json(client, "sensors/imu/euler", {
        "yaw": euler[0],
        "roll": euler[1],
        "pitch": euler[2],
    })

    time.sleep(0.05)
    client.loop(0.05)
