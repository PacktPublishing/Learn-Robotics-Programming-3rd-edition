from deploy import virtual_env
from pyinfra.operations import files, systemd
from pyinfra import host


services = {
    "inventor_hat_service": ("robot/inventor_hat_service.py", True),
    "launcher_service": ("robot/launcher_service.py", True),
    "behavior_path": ("robot/behavior_path.py", False),
}

for service_name, (service_file, auto_start) in services.items():
    code = files.put(
        name=f"Update {service_name} code",
        src=service_file,
        dest=service_file,
    )

    # Create the service unit file
    service = files.template(
        name=f"Create {service_name} service",
        src=f"deploy/{service_name}.j2",
        dest=f"/etc/systemd/system/{service_name}.service",
        mode="644",
        user="root",
        group="root",
        pi_user=host.data.get('ssh_user'),
        _sudo=True
    )

    if code.changed or service.changed:
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
