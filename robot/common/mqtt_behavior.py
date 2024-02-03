import paho.mqtt.client as mqtt
import time

env = {
    "MQTT_HOSTNAME": "localhost",
    "MQTT_USERNAME": "robot",
    "MQTT_PASSWORD": "robot",
}

def default_on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def connect(on_connect=default_on_connect, start_loop=True):
    client = mqtt.Client()
    client.on_connect = on_connect
    print("Attempting to connect to " + env["MQTT_HOSTNAME"])
    client.username_pw_set(env["MQTT_USERNAME"], env["MQTT_PASSWORD"])
    client.will_set("motors/stop", "")
    client.connect(env["MQTT_HOSTNAME"], 1883)

    if start_loop:
        client.loop_start()
        while not client.is_connected():
            time.sleep(0.01)
    return client
