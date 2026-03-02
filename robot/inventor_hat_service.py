import atexit
import json
import time

import inventorhatmini
from common.mqtt_behavior import publish_json, connect

last_message = 0


board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]
left_distance_scale = 1.00
right_distance_scale = 0.985
left_encoder = board.encoders[1]
left_encoder.counts_per_rev(int(32 * 120 * left_distance_scale))
right_encoder = board.encoders[0]
right_encoder.counts_per_rev(int(32 * 120 * right_distance_scale))
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
        servo.value(position)
    except OSError:
        print("Error: Failed to set servo position")
    except ValueError:
        print("Error: Invalid position value")


def set_pan(client, userdata, msg):
    set_servo_position(pan, client, userdata, msg, fine_tune=5)


def set_tilt(client, userdata, msg):
    set_servo_position(tilt, client, userdata, msg, fine_tune=0)


def stop_servo(servo):
    if servo.is_enabled():
        servo.disable()


def stop_pan(client=None, userdata=None, msg=None):
    stop_servo(pan)


def stop_tilt(client=None, userdata=None, msg=None):
    stop_servo(tilt)


def set_motor_wheels(client, userdata, msg):
    left, right = json.loads(msg.payload)
    left_motor.enable()
    left_motor.speed(left)
    right_motor.enable()
    right_motor.speed(right)


def stop_motors(client=None, userdata=None, msg=None):
    left_motor.stop()
    right_motor.stop()
    stop_pan()
    stop_tilt()


def set_led(client, userdata, msg):
    index, r, g, b = json.loads(msg.payload)
    board.leds.set_rgb(index, r, g, b)


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


class EncoderState:
    seq = 0


def update_encoders(client):
    left_data = left_encoder.capture()
    right_data = right_encoder.capture()
    EncoderState.seq += 1
    publish_json(
        client,
        "sensors/encoders/data",
        {
            "seq": EncoderState.seq,
            "timestamp_ms": int(time.time() * 1000),
            "left_counts": left_data.count,
            "right_counts": right_data.count,
            "left_radians": left_data.radians,
            "right_radians": right_data.radians,
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

client = connect(on_connect=on_connect, start_loop=False)
client.message_callback_add("motors/#", all_messages)
client.message_callback_add("motors/stop", stop_motors)
client.message_callback_add("motors/wheels", set_motor_wheels)
client.message_callback_add("leds/#", all_messages)
client.message_callback_add("leds/set", set_led)

client.message_callback_add("motors/servo/pan/position", set_pan)
client.message_callback_add("motors/servo/pan/stop", stop_pan)
client.message_callback_add("motors/servo/tilt/position", set_tilt)
client.message_callback_add("motors/servo/tilt/stop", stop_tilt)
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
    time.sleep(0.1)
