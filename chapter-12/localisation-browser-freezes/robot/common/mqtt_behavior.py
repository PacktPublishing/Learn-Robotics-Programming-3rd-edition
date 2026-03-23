import paho.mqtt.client as mqtt
import time
import ujson as json

def load_config(config_path='robot_control/.env.json'):
    """Load configuration from .env.json file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def default_on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

def default_on_disconnect(client, userdata, rc):
    print(f"Disconnected with result code {rc}")
    if rc != 0:
        print("Unexpected disconnection, attempting to reconnect...")
        client.reconnect()

def connect(on_connect=default_on_connect, start_loop=True, config_path=None):
    print("Using details from env config")
    env_config = load_config(config_path) if config_path else load_config()
    mqtt_username = env_config["MQTT_USERNAME"]
    mqtt_password = env_config["MQTT_PASSWORD"]

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = default_on_disconnect
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
