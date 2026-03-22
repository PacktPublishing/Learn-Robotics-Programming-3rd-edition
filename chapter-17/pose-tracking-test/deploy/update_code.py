from pyinfra.operations import files

files.sync(
    src="robot", dest="robot", delete=True,
    exclude=("*.pyc", "**/*.pyc", "__pycache__", "**/__pycache__", "**/__pycache__/*"))
