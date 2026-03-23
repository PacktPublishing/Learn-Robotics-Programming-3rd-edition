from pyinfra.operations import files, systemd
from pyinfra import host

common = files.sync(
    src="robot/common", dest="robot/common")

services = [
    ["inventor_hat_service", "robot/inventor_hat_service.py", True],
    ["launcher_service", "robot/launcher_service.py", True],
    ["distance_sensor_service", "robot/distance_sensor_service.py", True],
    ["distance_plotter_service", "robot/distance_plotter.py", True],
    ["encoder_plotter_service", "robot/encoder_plotter.py", True],
    ["behavior_path", "robot/behavior_path.py", False],
    ["behavior_line", "robot/behavior_line.py", False],
    ["bang_bang_obstacle_avoiding", "robot/bang_bang_obstacle_avoiding.py", False],
    ["proportional_obstacle_avoiding", "robot/proportional_obstacle_avoiding.py", False],
    ["line_with_correction", "robot/line_with_correction.py", False],
]

for service_name, service_file, auto_start in services:
    code = files.put(
        name=f"Update {service_name} code",
        src=service_file,
        dest=service_file,
    )

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

    if ((code.changed or common.changed) and auto_start) or service.changed:
        # Restart the service
        systemd.service(
            name=f"Restart {service_name} service",
            service=service_name,
            running=auto_start,
            enabled=auto_start,
            restarted=auto_start,
            daemon_reload=service.changed,
            _sudo=True,
        )
