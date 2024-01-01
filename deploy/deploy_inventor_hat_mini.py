from deploy import virtual_env
from pyinfra.operations import apt, pip, files
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

# Create the service unit file
files.template(
    name="Create inventor HAT mini service",
    src="deploy/inventor_hat_mini.j2",
    dest="/etc/systemd/system/inventor_hat_mini.service",
    mode="644",
    user="root",
    group="root",
    pi_user=host.data.get('ssh_user'),
    _sudo=True
)