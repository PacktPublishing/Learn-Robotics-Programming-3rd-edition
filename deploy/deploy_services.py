from pyinfra.operations import files, systemd
from pyinfra import host
from deploy import update_code

services = [
    ["inventor_hat_service", "robot/inventor_hat_service.py", True],
    ["launcher_service", "robot/launcher_service.py", True],
    ["distance_sensor_service", "robot/distance_sensor_service.py", True],
    ["behavior_path", "robot/behavior_path.py", False],
]

for service_name, service_file, auto_start in services:
    # Create the service unit file
    if auto_start:
        restart="always"
    else:
        restart="no"

    service = files.template(
        name=f"Create {service_name} service",
        src="deploy/service_template.j2",
        dest=f"/etc/systemd/system/{service_name}.service",
        mode="644",
        user="root",
        group="root",
        pi_user=host.data.get('ssh_user'),
        service_name=service_name,
        service_file=service_file,
        restart=restart,
        _sudo=True
    )

    if update_code.code.changed or service.changed:
        # Restart the service
        systemd.service(
            name=f"Restart {service_name} service",
            service=service_name,
            running=auto_start,
            enabled=auto_start,
            restarted=auto_start,
            daemon_reload=True,
            _sudo=True,
        )
