import atexit
import json
import time

import inventorhatmini
import paho.mqtt.client as mqtt

last_message = 0
board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]
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


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("motors/#")
    client.subscribe("leds/#")
    client.subscribe("all/#")


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
client.message_callback_add("motors/servo/pan/position", set_pan)
client.message_callback_add("motors/servo/pan/stop", stop_pan)
client.message_callback_add("motors/servo/tilt/position", set_tilt)
client.message_callback_add("motors/servo/tilt/stop", stop_tilt)
client.message_callback_add("all/stop", stop_motors)
client.message_callback_add("all/#", all_messages)

client.connect("localhost", 1883)
board.leds.set_rgb(0, 0, 255, 0)

client.loop_start()
while True:
    if board.switch_pressed():
        client.publish("launcher/poweroff", "")
    if time.time() - last_message > 1:
        stop_motors()
    time.sleep(0.1)
