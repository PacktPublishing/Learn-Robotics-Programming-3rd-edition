# from pyinfra.operations import server
# from deploy import virtual_env
from pyinfra.operations import apt
# , pip


apt.packages(
    name = "Install Camera packages",
    packages = ["python3-picamera2", "python3-opencv", "opencv-data", "python3-flask"],
    no_recommends=True,
    _sudo = True
)

