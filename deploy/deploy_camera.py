# from pyinfra.operations import server
# from deploy import virtual_env
from pyinfra.operations import apt
# , pip


apt.packages(
    name = "Install python3-picamera2",
    packages = ["python3-picamera2"],
    _sudo = True
)

