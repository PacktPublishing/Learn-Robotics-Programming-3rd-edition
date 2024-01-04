from pyinfra.operations import files

code = files.sync(src="robot", dest="robot", delete=True)
