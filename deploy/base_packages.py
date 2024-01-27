from pyinfra.operations import apt

base_packages = apt.packages(
    name="Install python and i2c tools",
    packages=["python3-pip", "python3-smbus", "i2c-tools", "python3-numpy"],
    _sudo=True,
)

apt_packages = apt.packages(
    name="Install apt dependencies for services",
    packages=["python3-matplotlib", "python3-numpy", "python3-ujson"],
    _sudo=True,
)
