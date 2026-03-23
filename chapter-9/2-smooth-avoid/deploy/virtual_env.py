from io import BytesIO

from pyinfra.facts.server import Home
from pyinfra import host
from pyinfra.operations import apt, pip, files

from deploy import base_packages

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

robotpython = f"""\
#!/bin/bash
{robot_venv}/bin/python3 $@
"""

files.put(
    name="Create robotpython script",
    src=BytesIO(robotpython.encode("utf-8")),
    mode="755",
    dest="/usr/local/bin/robotpython", _sudo=True,
)

pip.packages(
    name="Install pip dependencies for services",
    packages=["vl53l5cx-ctypes", "bokeh"],
    virtualenv=robot_venv,
)
