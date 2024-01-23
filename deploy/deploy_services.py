from pyinfra.operations import files, systemd, pip, apt
from pyinfra import host
from deploy import update_code, virtual_env


pip_packages = pip.packages(
    name="Install pip dependencies for services",
    packages=["vl53l5cx-ctypes", "quart"],
    virtualenv=virtual_env.robot_venv,
)

apt_packages = apt.packages(
    name="Install apt dependencies for services",
    packages=["python3-matplotlib", "python3-numpy"],
    _sudo=True,
)

services = [
    ["inventor_hat_service", "robot/inventor_hat_service.py", True],
    ["launcher_service", "robot/launcher_service.py", True],
    ["distance_sensor_service", "robot/distance_sensor_service.py", True],
    ["distance_plotter_service", "robot/distance_plotter.py", True],
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

    if update_code.code.changed or pip_packages.changed or apt_packages.changed or service.changed:
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
