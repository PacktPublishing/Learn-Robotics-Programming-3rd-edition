import atexit
import json
import inventorhatmini
import paho.mqtt.client as mqtt
import time

last_message = 0
board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]


def all_messages(client, userdata, msg):
    global last_message
    last_message = time.time()
    print(f"{msg.topic} {msg.payload}")


def set_motor_wheels(client, userdata, msg):
    left, right = json.loads(msg.payload)
    left_motor.enable()
    left_motor.speed(left)
    right_motor.enable()
    right_motor.speed(right)


def stop_motors(client=None, userdata=None, msg=None):
    left_motor.stop()
    right_motor.stop()


def set_led(client, userdata, msg):
    index, r, g, b = json.loads(msg.payload)
    board.leds.set_rgb(index, r, g, b)


def set_led(client, userdata, msg):
    index, r, g, b = json.loads(msg.payload)
    board.leds.set_rgb(index, r, g, b)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("motors/#")
    client.subscribe("leds/#")

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
client.message_callback_add("leds/#", all_messages)
client.message_callback_add("leds/set", set_led)
client.message_callback_add("all/stop", stop_motors)

client.message_callback_add("leds/#", print_message)
client.message_callback_add("leds/set", set_led)

client.connect("localhost", 1883)
board.leds.set_rgb(0, 0, 90, 0)
client.loop_start()
while True:
    if time.time() - last_message > 1:
        stop_motors()
    time.sleep(0.1)
