from deploy import virtual_env
from pyinfra.operations import pip, server

piper = pip.packages(
    name="Install piper TTS Python packages",
    packages=[
        "piper-tts",
        "sounddevice",
    ],
    virtualenv=virtual_env.robot_venv,
)

if piper.changed:
    server.shell("robotpython -m piper.download_voices en_US-ryan-low")

pip.packages(
    name="Install vosk recognition",
    packages=[
        "vosk",
    ],
    virtualenv=virtual_env.robot_venv
)
