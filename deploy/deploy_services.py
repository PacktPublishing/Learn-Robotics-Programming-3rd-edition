from pyinfra.operations import files, systemd
from pyinfra import host

def deploy_service(service_name, command, auto_start, changed):
    if auto_start:
        restart="always"
    else:
        restart="no"

    unit_file = files.template(
        name=f"Create {service_name} service",
        src="deploy/service_template.j2",
        dest=f"/etc/systemd/system/{service_name}.service",
        pi_user=host.data.get('ssh_user'),
        service_name=service_name,
        command=command,
        restart=restart,
        _sudo=True
    )
        
    if changed or code.changed or unit_file.changed:
        systemd.service(
            name=f"Restart {service_name} service",
            service=service_name,
            running=auto_start,
            enabled=auto_start,
            restarted=auto_start,
            daemon_reload=unit_file.changed,
            _sudo=True,
        )

common = files.sync(
    name="Update common code",
    src="robot/common", dest="robot/common")

code = files.put(
    name="Update inventor hat code",
    src="robot/inventor_hat_service.py", dest="robot/inventor_hat_service.py")

deploy_service("inventor_hat_service","robot/inventor_hat_service.py", 
               True, common.changed or code.changed)
