import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

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

client.publish("motors/left", 0.8)
client.publish("motors/right", 0.8)
time.sleep(2)
client.publish("motors/stop", "")

client.loop_stop()
