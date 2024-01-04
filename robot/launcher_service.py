import atexit
import json
import subprocess
import paho.mqtt.client as mqtt


mqtt_username = "robot"
mqtt_password = "robot"

def print_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")

registered_units = ["behavior_path.service"]

def start_systemd_unit(client, userdata, msg):
    unit_name = msg.payload.decode()
    if unit_name in registered_units:
        subprocess.run(["systemctl", "start", unit_name])
        client.publish(f"launcher/{unit_name}/status", "started")
    else:
        print(f"Unit {unit_name} is not registered")
        client.publish(f"err/launcher", f"{unit_name} not registered")

def stop_systemd_unit(client, userdata, msg):
    unit_name = msg.payload.decode()
    if unit_name in registered_units:
        subprocess.run(["systemctl", "stop", unit_name])
        client.publish(f"launcher/{unit_name}/status", "stopped")
    else:
        print(f"Unit {unit_name} is not registered")
        client.publish(f"err/launcher", f"{unit_name} not registered")


def poweroff(client, userdata, msg):
    print("Powering off")
    subprocess.run(["poweroff"])

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("launcher/#")
    client.publish("leds/set", "[1, 0, 0, 255]")

client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)
client.on_connect = on_connect

client.message_callback_add("launcher/#", print_message)
client.message_callback_add("launcher/start", start_systemd_unit)
client.message_callback_add("launcher/stop", stop_systemd_unit)
client.message_callback_add("launcher/poweroff", poweroff)

client.connect("localhost", 1883)
client.loop_forever()
