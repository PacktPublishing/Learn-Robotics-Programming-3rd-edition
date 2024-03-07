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

files.file(
    name="Create robotpython script",
    path="/usr/local/bin/robotpython",
    mode="755",
    _sudo=True,
)

files.block(
    name="Setup robotpython script content",
    path="/usr/local/bin/robotpython",
    content=f"""
        #!/bin/bash
        {robot_venv}/bin/python3 $@
    """,
    try_prevent_shell_expansion=True,
    _sudo=True,
)

pip.packages(
    name="Install pip dependencies for services",
    packages=["vl53l5cx-ctypes", "bokeh"],
    virtualenv=robot_venv,
)
