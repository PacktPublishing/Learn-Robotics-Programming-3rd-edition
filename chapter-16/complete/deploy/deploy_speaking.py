from deploy import virtual_env
from pyinfra.operations import apt, pip, server

audio_packages = apt.packages(
    name="Install audio hardware packages",
    packages=[
        "libportaudio2",
        "pipewire-alsa",
    ],
    _sudo=True
)

piper = pip.packages(
    name="Install piper TTS Python packages",
    packages=[
        "piper-tts",
        "pathvalidate",
        "sounddevice",
    ],
    virtualenv=virtual_env.robot_venv
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
