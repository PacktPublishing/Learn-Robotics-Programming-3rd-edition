from pyinfra.operations import server

server.shell(
    name="Disable Wi-Fi power save on wlan0",
    commands=[
        "if command -v iw >/dev/null 2>&1; then iw dev wlan0 set power_save off; else echo 'iw not installed, skipping'; fi"
    ],
    _sudo=True,
)
