from pyinfra.operations import files, systemd
from pyinfra import host

service_name = "inventor_hat_service"
python_file = "robot/inventor_hat_service.py"
auto_start = True

common = files.sync(
    name="Update common code",
    src="robot/common", dest="robot/common")

code = files.put(
    name=f"Update {service_name} code",
    src=python_file,
    dest=python_file,
)

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
    systemd.service(
        name=f"Restart {service_name} service",
        service=service_name,
        running=auto_start,
        enabled=auto_start,
        restarted=auto_start,
        daemon_reload=unit_file.changed,
        _sudo=True,
    )
