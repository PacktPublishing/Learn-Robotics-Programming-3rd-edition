from pyinfra.operations import systemd

systemd.service(
    name="Stop inventor hat service",
    service="inventor_hat_service",
    running=False,
    _sudo=True
)
systemd.service(
    name="Stop distance sensor service",
    service="distance_sensor_service",
    running=False,
    _sudo=True
)

systemd.service(
    name="Stop IMU service",
    service="imu_service",
    running=False,
    _sudo=True
)
