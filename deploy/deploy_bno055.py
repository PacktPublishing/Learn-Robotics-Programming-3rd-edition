from pyinfra.operations import pip
from deploy import virtual_env

pip.packages(
    name="Install BNO055 dependencies",
    packages=["Adafruit-Blinka", "adafruit-circuitpython-bno055"],
    virtualenv=virtual_env.robot_venv,
)
