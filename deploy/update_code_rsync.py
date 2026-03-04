from pyinfra.operations import files

files.rsync(
    src="robot/",
    dest="robot/",
    flags=[
        "--archive",
        "--delete",
        "--exclude=__pycache__/",
        "--exclude=*.pyc",
    ],
)
