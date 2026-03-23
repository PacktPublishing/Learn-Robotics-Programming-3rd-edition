from pyinfra.operations import apt

base_packages = apt.packages(
    name="Install python and i2c tools",
    packages=["python3-pip", "python3-smbus", "i2c-tools"],
    _sudo=True,
)
