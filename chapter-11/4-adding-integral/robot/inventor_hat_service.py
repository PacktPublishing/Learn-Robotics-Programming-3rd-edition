import atexit
import json
import time
from functools import partial

import inventorhatmini
import paho.mqtt.client as mqtt
from common.mqtt_behavior import publish_json

last_message = 0
board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]
left_encoder = board.encoders[1]
left_encoder.counts_per_rev(32 * 120)
right_encoder = board.encoders[0]
right_encoder.counts_per_rev(32 * 120)
wheel_radius = 67 / 2
pan = board.servos[0]
tilt = board.servos[1]


def all_messages(client, userdata, msg):
    global last_message
    last_message = time.time()
    print(f"{msg.topic} {msg.payload}")


def set_servo_position(servo, client, userdata, msg, fine_tune=0):
    try:
        position = float(msg.payload) + fine_tune
        # servo.enable()
        servo.value(position)
    except OSError:
        print("Error: Failed to set servo position")
    except ValueError:
        print("Error: Invalid position value")


def stop_servo(servo, client=None, userdata=None, msg=None):
    if servo.is_enabled():
        servo.disable()


def set_motor_wheels(client, userdata, msg):
    left, right = json.loads(msg.payload)
    left_motor.enable()
    left_motor.speed(left)
    right_motor.enable()
    right_motor.speed(right)


def stop_motors(client=None, userdata=None, msg=None):
    left_motor.stop()
    right_motor.stop()
    stop_servo(pan)
    stop_servo(tilt)


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("motors/#")
    client.subscribe("leds/#")
    client.subscribe("all/#")
    client.subscribe("sensors/encoders/control/#")


def reset_encoders(*_):
    print("Reset called")
    left_encoder.zero()
    right_encoder.zero()


def update_encoders(client):
    left_data = left_encoder.capture()
    right_data = right_encoder.capture()
    publish_json(
        client,
        "sensors/encoders/data",
        {
            "left_distance": left_data.radians * wheel_radius,
            "right_distance": right_data.radians * wheel_radius,
            "left_mm_per_sec": left_data.radians_per_second * wheel_radius,
            "right_mm_per_sec": right_data.radians_per_second * wheel_radius,
        }
    )


def exit_handler():
    stop_motors()
    board.leds.clear()


atexit.register(exit_handler)

mqtt_username = "robot"
mqtt_password = "robot"

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)
client.on_connect = on_connect

client.message_callback_add("motors/#", all_messages)
client.message_callback_add("motors/stop", stop_motors)
client.message_callback_add("motors/wheels", set_motor_wheels)
client.message_callback_add("motors/servo/pan/position",
                            partial(set_servo_position, pan,
                                    fine_tune=5))
client.message_callback_add("motors/servo/pan/stop",
                            partial(stop_servo, pan))
client.message_callback_add("motors/servo/tilt/position",
                            partial(set_servo_position, tilt,
                                    fine_tune=0))
client.message_callback_add("motors/servo/tilt/stop",
                            partial(stop_servo, tilt))
client.message_callback_add("all/stop", stop_motors)
client.message_callback_add("all/#", all_messages)
client.message_callback_add("sensors/encoders/control/reset", reset_encoders)

client.connect("localhost", 1883)
board.leds.set_rgb(0, 0, 255, 0)

client.loop_start()
while True:
    update_encoders(client)
    if board.switch_pressed():
        client.publish("launcher/poweroff", "")
    if time.time() - last_message > 1:
        stop_motors()
    time.sleep(0.05)
