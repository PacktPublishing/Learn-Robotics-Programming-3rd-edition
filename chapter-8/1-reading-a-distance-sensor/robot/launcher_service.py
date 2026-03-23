import subprocess
from common.mqtt_behavior import connect, publish_json


def print_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")

def start_systemd_unit(client, userdata, msg):
    unit_name = msg.payload.decode()
    subprocess.run(["systemctl", "start", unit_name])
    print(unit_name, "started")

def stop_systemd_unit(client, userdata, msg):
    unit_name = msg.payload.decode()
    subprocess.run(["systemctl", "stop", unit_name])
    print(unit_name, "stopped")

def poweroff(client, userdata, msg):
    print("Powering off")
    subprocess.run(["poweroff"])

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("launcher/#")
    publish_json(client, "leds/set", [1, 0, 0, 255])


client = connect(on_connect=on_connect, start_loop=False)

client.message_callback_add("launcher/#", print_message)
client.message_callback_add("launcher/start", start_systemd_unit)
# client.message_callback_add("launcher/stop", stop_systemd_unit)
client.message_callback_add("launcher/poweroff", poweroff)

client.loop_forever()
