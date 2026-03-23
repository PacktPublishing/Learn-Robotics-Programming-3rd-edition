from pyinfra.operations import \
    apt, systemd, server, files, pip
from deploy import virtual_env

server.shell(
    name="Ensure ollama is installed",
    commands=[
        "(which ollama && ollama -v) || (curl -fsSL https://ollama.com/install.sh | sh)"
    ],
    _sudo=True,
)
## Can i make it an operation - with a check, and an action?
## It has installed ollama
## Watch the learning curve...
modelfile = files.put(
    name="Update the Modelfile",
    src="robot/voice/Modelfile",
    dest="robot/voice/Modelfile",
)

# run with pyinfra inventory.py deploy/deploy_voice.py -y -v
if modelfile.changed:
    server.shell(
        name="Prepare the model",
        commands=[
            "ollama create robot-intent-1b -f robot/voice/Modelfile"
        ],
    )

# Then run update code...
pip.packages(
    name="Install ollama python client",
    packages=[
        "ollama"
    ],
    virtualenv=virtual_env.robot_venv,
)
