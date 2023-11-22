from pyinfra.operations import files

files.sync("robot", "robot", delete=True)
