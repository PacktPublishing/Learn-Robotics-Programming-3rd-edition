from pyinfra.operations import files

files.sync(src="robot", dest="robot", delete=True)
