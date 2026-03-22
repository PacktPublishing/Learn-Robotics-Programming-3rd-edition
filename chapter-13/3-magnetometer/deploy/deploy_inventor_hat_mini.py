from deploy import virtual_env
from pyinfra.operations import apt, pip

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
