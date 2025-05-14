# from deploy.virtual_env import robot_venv
from pyinfra.operations import apt, pip, files

# from pyinfra.operations import apt

base_packages = apt.packages(
    name="Install AI packages",
    packages=["python3-picamera2", "python3-opencv", "opencv-data",
              "python3-flask"],
    update=True,
    no_recommends=True,
    _sudo=True,
)

# pip.packages(
#     name="Install pip dependencies for services",
#     packages=["torch", "torchvision"],
#     virtualenv=robot_venv,
# )


files.download(
    name="Download Face detection model",
    # Go to https://github.com/opencv/opencv_zoo/blob/main/models/face_detection_yunet/face_detection_yunet_2023mar_int8.onnx, and right click on RAW
    src="https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar_int8.onnx",
    dest="face_detection_yunet_2023mar_int8.onnx"
)
