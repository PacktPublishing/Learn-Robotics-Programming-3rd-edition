from pyinfra.operations import pip
from deploy import virtual_env

pip.packages(
    name="Install distance sensor dependencies",
    packages=["vl53l5cx-ctypes"],
    virtualenv=virtual_env.robot_venv,
)
