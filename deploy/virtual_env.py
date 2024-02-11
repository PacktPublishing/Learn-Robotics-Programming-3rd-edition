from deploy import base_packages
from pyinfra.facts.server import Home
from pyinfra import host
from pyinfra.operations import apt, pip, files

apt.packages(
    name="Install python venv tool",
    packages=["python3-venv"],
    _sudo=True,
)

robot_venv = f"{host.get_fact(Home)}/robotvenv"
pip.venv(
    name="Robot python virtual environment",
    path=robot_venv,
    site_packages=True,
)

