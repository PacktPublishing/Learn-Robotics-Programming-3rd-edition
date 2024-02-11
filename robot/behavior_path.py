from time import sleep
from common.mqtt_behavior import connect

def forward(client, seconds):
    client.publish("motors/left", 0.8)
    client.publish("motors/right", 0.8)
    sleep(seconds)

def drive_left(client, seconds):
    client.publish("motors/left", 0.2)
    client.publish("motors/right", 0.8)
    sleep(seconds)

def drive_right(client, seconds):
    client.publish("motors/left", 0.8)
    client.publish("motors/right", 0.2)
    sleep(seconds)

def spin_left(client, seconds):
    client.publish("motors/left", -0.8)
    client.publish("motors/right", 0.8)
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
