from pyinfra.operations import apt, files

apt.packages(
    name="Install AI packages",
    packages=["python3-picamera2", "python3-opencv", "opencv-data",
              "python3-flask"],
    no_recommends=True,
    _sudo=True,
)

files.download(
    name="Download Face detection model",
    src="https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar_int8.onnx",
    dest="face_detection_yunet_2023mar_int8.onnx"
)
