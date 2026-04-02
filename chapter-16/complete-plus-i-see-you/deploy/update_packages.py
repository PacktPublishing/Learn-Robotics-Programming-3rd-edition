from pyinfra.operations import apt

apt.update(
    name="Update apt cache",
    _sudo=True,
)

upgrade = apt.upgrade(
    name="Upgrade all packages",
    dist=True,
    _sudo=True,
)
