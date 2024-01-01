from deploy import virtual_env
from pyinfra.operations import apt, pip, files, systemd
from pyinfra import host

apt.packages(
    name = "Install smbus2",
    packages = ["python3-smbus2"],
    _sudo = True
)

pip.packages(
    name="Install Inventor hat mini",
    packages=[
        "inventorhatmini",
    ],
    virtualenv=virtual_env.robot_venv,
)

code = files.put(
    name="Update Inventor HAT mini code",
    src="robot/inventor_hat_service.py",
    dest="robot/inventor_hat_service.py",
)

# Create the service unit file
service = files.template(
    name="Create inventor HAT mini service",
    src="deploy/inventor_hat_mini.j2",
    dest="/etc/systemd/system/inventor_hat_mini.service",
    mode="644",
    user="root",
    group="root",
    pi_user=host.data.get('ssh_user'),
    _sudo=True
)

if code.changed or service.changed:
    # Restart the service
    systemd.service(
        name="Restart inventor HAT mini service",
        service="inventor_hat_mini",
        running=True,
        restarted=True,
        daemon_reload=True,
        _sudo=True,
    )
