from deploy import virtual_env
from pyinfra.operations import apt, pip, files, server, systemd

apt.packages(
    name="Install speech recognition Apt packages",
    packages=["python3-pyaudio"],
    _sudo=True,
)

# Ensure you use the device index corresponding with a default, having made an asoundrc work for the device.
# Dont do the raspiconfig thing - it may be what made that mess in the lib/alsa/conf.d files.

pip.packages(
    name="Install speech recognition Python packages",
    packages=[
        "vosk", "SpeechRecognition"
    ],
    virtualenv=virtual_env.robot_venv,
)

model_file = files.download(
    name="Download vosk model",
    src="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    dest="vosk-model-small-en-us-0.15.zip",
)

if model_file.changed:
    # unzip the model file
    server.shell(
        name="Unzip vosk model",
        commands=[
            "unzip vosk-model-small-en-us-0.15.zip",
        ],
    )
    # Rename to model
    server.shell(
        name="Rename vosk model",
        commands=[
            "mv vosk-model-small-en-us-0.15 model",
        ],
    )

# TODO: Automate the asoundrc file creation.
