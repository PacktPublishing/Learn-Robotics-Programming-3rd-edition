from pyinfra.operations import files, systemd
from pyinfra import host
from deploy import deploy_web_server


common = files.sync(
    src="robot/common", dest="robot/common")

services = [
    ["inventor_hat_service", "robot/inventor_hat_service.py", True],
    ["launcher_service", "robot/launcher_service.py", True],
    ["behavior_path", "robot/behavior_path.py", False],
]

for service_name, python_file, auto_start in services:
    code = files.put(
        name=f"Update {service_name} code",
        src=python_file,
        dest=python_file,
    )

    # Create the service unit file
    if auto_start:
        restart="always"
    else:
        restart="no"

    unit_file = files.template(
        name=f"Create {service_name} service",
        src="deploy/service_template.j2",
        dest=f"/etc/systemd/system/{service_name}.service",
        pi_user=host.data.get('ssh_user'),
        service_name=service_name,
        command=python_file,
        restart=restart,
        _sudo=True
    )

    if code.changed or common.changed or unit_file.changed:
        # Restart the service
        systemd.service(
            name=f"Restart {service_name} service",
            service=service_name,
            running=auto_start,
            enabled=auto_start,
            restarted=auto_start,
            daemon_reload=unit_file.changed,
            _sudo=True,
        )
