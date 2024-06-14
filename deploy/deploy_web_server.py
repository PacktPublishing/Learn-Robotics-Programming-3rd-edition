from pyinfra.operations import files, systemd
from pyinfra import host

html = files.sync("robot_control", "robot_control")
web_server_unit_file = files.template(
    name="Create web service",
    src="deploy/service_template.j2",
    dest="/etc/systemd/system/web_server.service",
    pi_user=host.data.get('ssh_user'),
    service_name="web_server",
    command="-m http.server --directory robot_control",
    restart=True,
    _sudo=True
)
if web_server_unit_file.changed:
    systemd.service(
        name="Restart web service",
        service="web_server",
        running=True,
        enabled=True,
        restarted=True,
        daemon_reload=web_server_unit_file.changed,
        _sudo=True,
    )