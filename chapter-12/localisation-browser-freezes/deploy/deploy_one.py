"""Deploy a single service quickly - specify which one with --data service=<name>."""
from pyinfra.operations import files, systemd
from pyinfra import host

# Get the service name from command line: --data service=localisation
service = host.data.get('service')

if not service:
    raise ValueError("Must specify service with --data service=<service_name>")

# Map service names to their files
service_files = {
    'inventor_hat_service': 'robot/inventor_hat_service.py',
    'wheel_control_service': 'robot/wheel_control_service.py',
    'launcher_service': 'robot/launcher_service.py',
    'config_store': 'robot/config_store.py',
    'behavior_path': 'robot/behavior_path.py',
    'drive_known_distance': 'robot/drive_known_distance.py',
    'circle_head': 'robot/circle_head_behavior.py',
    'distance_sensor_service': 'robot/distance_sensor_service.py',
    'fixed_distance_avoider': 'robot/fixed_distance_avoider.py',
    'smooth_distance_avoider': 'robot/smooth_distance_avoider.py',
    'localisation': 'robot/localisation.py',
}

if service not in service_files:
    raise ValueError(f"Unknown service: {service}. Valid services: {', '.join(service_files.keys())}")

# Always sync common folder (it's fast if nothing changed)
files.sync(
    name="Update common code",
    src="robot/common",
    dest="robot/common"
)

# Upload the specific service file
files.put(
    name=f"Update {service} code",
    src=service_files[service],
    dest=service_files[service]
)

# Restart the service
systemd.service(
    name=f"Restart {service}",
    service=service,
    restarted=True,
    _sudo=True,
)
