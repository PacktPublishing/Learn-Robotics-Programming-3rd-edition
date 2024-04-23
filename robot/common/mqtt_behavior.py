import paho.mqtt.client as mqtt
import time
import json

def default_on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def connect(on_connect=default_on_connect, start_loop=True):
    mqtt_username = "robot"
    mqtt_password = "robot"

    client = mqtt.Client()
    client.on_connect = on_connect
    client.username_pw_set(mqtt_username, mqtt_password)
    client.will_set("all/stop", "")
    client.connect("localhost", 1883)

    if start_loop:
        client.loop_start()
        while not client.is_connected():
            time.sleep(0.01)
    return client

def publish_json(client, topic, data):
    client.publish(topic, json.dumps(data))

def subscribe(client, topic, callback):
    client.subscribe(topic)
    client.message_callback_add(topic, callback)
