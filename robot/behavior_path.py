from time import sleep
from common.mqtt_behavior import connect, publish_json
import json

def forward(client, seconds):
    publish_json(client, "motors/wheels", [0.8, 0.8])
    sleep(seconds)

def drive_left(client, seconds):
    publish_json(client, "motors/wheels", [0.2, 0.8])
    sleep(seconds)

def drive_right(client, seconds):
    publish_json(client, "motors/wheels", [0.8, 0.2])
    sleep(seconds)

def spin_left(client, seconds):
    publish_json(client, "motors/wheels", [-0.8, 0.8])
    sleep(seconds)

client = connect()
forward(client, 1)
drive_right(client, 1)
forward(client, 1)
drive_left(client, 1)
forward(client, 1)
drive_left(client, 1)
forward(client, 1)
spin_left(client, 1)
client.publish("motors/stop", "")
client.loop_stop()
