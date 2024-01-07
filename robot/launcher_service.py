import subprocess
import paho.mqtt.client as mqtt


def print_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")

def start_systemd_unit(client, userdata, msg):
    unit_name = msg.payload.decode()
    subprocess.run(["systemctl", "start", unit_name])
    print(unit_name, "started")

def poweroff(client, userdata, msg):
    print("Powering off")
    subprocess.run(["poweroff"])

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("launcher/#")
    client.publish("leds/set", "[1, 0, 0, 255]")

mqtt_username = "robot"
mqtt_password = "robot"

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)
client.on_connect = on_connect

client.message_callback_add("launcher/#", print_message)
client.message_callback_add("launcher/start", start_systemd_unit)
client.message_callback_add("launcher/stop", stop_systemd_unit)
client.message_callback_add("launcher/poweroff", poweroff)

client.connect("localhost", 1883)
client.loop_forever()
