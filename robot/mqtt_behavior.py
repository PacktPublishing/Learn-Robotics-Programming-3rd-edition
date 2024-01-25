import paho.mqtt.client as mqtt
import time

def default_on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def connect(on_connect=default_on_connect):
    mqtt_username = "robot"
    mqtt_password = "robot"

    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.will_set("motors/stop", "")
    client.connect("localhost", 1883)

    client.loop_start()
    while not client.is_connected():
        time.sleep(0.01)
    return client
