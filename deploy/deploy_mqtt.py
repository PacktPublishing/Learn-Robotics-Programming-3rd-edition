from pyinfra.operations import \
    apt, systemd, server, files
import json


mosquitto_packages = apt.packages(
    name="Install mosquitto",
    packages=[
        "mosquitto",
        "mosquitto-clients",
        "python3-paho-mqtt"
    ],
    present=True, _sudo=True)

# Load MQTT credentials from .env.json
with open('.env.json', 'r') as f:
    env_config = json.load(f)

mqtt_username = env_config["MQTT_USERNAME"]
mqtt_password = env_config["MQTT_PASSWORD"]

# Deploy env file to track changes
env_file = files.put(
    name="Deploy MQTT environment config",
    src=".env.json",
    dest="/etc/mosquitto/.env.json",
    _sudo=True
)

if mosquitto_packages.changed or env_file.changed:
    # set mosquitto password
    server.shell(
        f"mosquitto_passwd -c -b /etc/mosquitto/passwd {mqtt_username} {mqtt_password}",
        _sudo=True)

mosquitto_files = files.put(
    name="Configure mosquitto",
    src="deploy/robot_mosquitto.conf",
    dest="/etc/mosquitto/conf.d/robot.conf",
    _sudo=True
)

if mosquitto_packages.changed or mosquitto_files.changed or env_file.changed:
    # restart mosquitto
    systemd.service(
        name="Restart/enable mosquitto",
        service="mosquitto",
        running=True,
        restarted=True,
        daemon_reload=True,
        _sudo=True,
    )
