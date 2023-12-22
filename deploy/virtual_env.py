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

# link that to make it easy
files.link(
    name="Link robotpython venv",
    target=f"{robot_venv}/bin/python3",
    path="/usr/local/bin/robotpython",
    _sudo=True,
)
