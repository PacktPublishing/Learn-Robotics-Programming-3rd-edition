import atexit
import json
import inventorhatmini
import paho.mqtt.client as mqtt

board = inventorhatmini.InventorHATMini()
left_motor = board.motors[1]
right_motor = board.motors[0]

def set_left_motor(client, userdata, msg):
    speed = json.loads(msg.payload)
    left_motor.enable()
    left_motor.speed(speed)

def set_right_motor(client, userdata, msg):
    speed = json.loads(msg.payload)
    right_motor.enable()
    right_motor.speed(speed)

def stop_motors(client=None, userdata=None, msg=None):
    left_motor.stop()
    right_motor.stop()

def print_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("motors/#")

def exit_handler():
    stop_motors()
    board.leds.clear()

atexit.register(exit_handler)

mqtt_username = "robot"
mqtt_password = "robot"

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)
client.on_connect = on_connect

client.message_callback_add("motors/#", print_message)
client.message_callback_add("motors/stop", stop_motors)
client.message_callback_add("motors/left", set_left_motor)
client.message_callback_add("motors/right", set_right_motor)

client.connect("localhost", 1883)
board.leds.set_rgb(0, 0, 255, 0)
client.loop_forever()
