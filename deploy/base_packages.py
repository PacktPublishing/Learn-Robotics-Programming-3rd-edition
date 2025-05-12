from turtle import update
from pyinfra.operations import apt

base_packages = apt.packages(
    name="Install python and i2c tools",
    packages=["python3-pip", "python3-smbus", "i2c-tools", "python3-ujson", "python3-numpy",
              "python3-picamera2", "python3-opencv", "opencv-data",
              "python3-flask"],
    update=True,
    no_recommends=True,
    _sudo=True,
)
