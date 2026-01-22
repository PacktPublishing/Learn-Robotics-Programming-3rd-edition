"""Launcher service adapted for supervisord in simulation environment."""
import subprocess
from common.mqtt_behavior import connect, publish_json


def print_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")


def start_supervisor_program(client, userdata, msg):
    """Start a supervisord program (equivalent to systemd unit)."""
    program_name = msg.payload.decode()
    try:
        result = subprocess.run(
            ["supervisorctl", "start", program_name],
            capture_output=True,
            text=True
        )
        print(f"{program_name} start result: {result.stdout}")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Failed to start {program_name}: {e}")


def stop_supervisor_program(client, userdata, msg):
    """Stop a supervisord program (equivalent to systemd unit)."""
    program_name = msg.payload.decode()
    try:
        result = subprocess.run(
            ["supervisorctl", "stop", program_name],
            capture_output=True,
            text=True
        )
        print(f"{program_name} stop result: {result.stdout}")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Failed to stop {program_name}: {e}")


def poweroff(client, userdata, msg):
    """Simulation poweroff - just log it."""
    print("Poweroff requested (simulation mode - ignoring)")
    publish_json(client, "launcher/status", {"status": "poweroff_requested"})


def on_connect(client, userdata, flags, rc):
    print(f"Launcher service connected with result code {rc}")
    client.subscribe("launcher/#")
    # Signal ready status (no LEDs in simulation)
    publish_json(client, "launcher/status", {"status": "ready"})


client = connect(on_connect=on_connect, start_loop=False)

client.message_callback_add("launcher/#", print_message)
client.message_callback_add("launcher/start", start_supervisor_program)
client.message_callback_add("launcher/stop", stop_supervisor_program)
client.message_callback_add("launcher/poweroff", poweroff)

print("Launcher service (supervisord mode) starting...")
client.loop_forever()
