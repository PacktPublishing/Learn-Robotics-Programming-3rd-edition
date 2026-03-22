from pyinfra.operations import \
    apt, systemd, server, files


mosquitto_packages = apt.packages(
    name="Install mosquitto", 
    packages=[
        "mosquitto", 
        "mosquitto-clients",
        "python3-paho-mqtt"
    ],
    present=True, _sudo=True)

mqtt_username = "robot"
mqtt_password = "robot"
if mosquitto_packages.changed:
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

if mosquitto_packages.changed or mosquitto_files.changed:
    # restart mosquitto
    systemd.service(
        name="Restart/enable mosquitto",
        service="mosquitto",
        running=True,
        restarted=True,
        daemon_reload=True,
        _sudo=True,
    )
