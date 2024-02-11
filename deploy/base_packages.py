from pyinfra.operations import apt

apt.packages(
    name="Install python and i2c tools",
    packages=["python3-pip", "python3-smbus", "i2c-tools",
              "python3-matplotlib", "python3-numpy", "python3-ujson"],
    _sudo=True,
)
