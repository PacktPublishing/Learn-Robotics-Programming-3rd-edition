"""Deploy web interface files only (HTML, JS, CSS)."""
from pyinfra.operations import files, systemd
import os


# Create robot_control directory
pages_folder = files.directory(
    name="Create robot_control folder",
    path="robot_control"
)

# Ensure libs directory exists
files.directory(
    name="Create robot_control/libs",
    path="robot_control/libs"
)

# Download external JS libraries (optional - only if they don't exist or need updating)
files.download(
    name="Download joystick widget",
    src="https://github.com/bobboteck/JoyStick/raw/master/joy.js",
    dest="robot_control/libs/joy.js"
)
files.download(
    name="Download mqtt js",
    src="https://unpkg.com/mqtt@5.7.0/dist/mqtt.esm.js",
    dest="robot_control/libs/mqtt.js"
)
files.download(
    name="Download chart js",
    src="https://cdn.jsdelivr.net/npm/chart.js",
    dest="robot_control/libs/chart.js"
)
files.download(
    name="Download chartjs datalabels plugin",
    src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2",
    dest="robot_control/libs/chartjs-plugin-datalabels"
)

# Deploy all files from robot_control directory
# This handles both regular files and Jinja2 templates
pages = [
    files.template(
        name=f"Deploy {file_name}",
        src=f"robot_control/{file_name}",
        dest=f"robot_control/{file_name}",
    )
    for file_name in os.listdir("robot_control")
    if os.path.isfile(f"robot_control/{file_name}")
]

pages_changed = pages_folder.changed or any(page.changed for page in pages)

# Restart web server if pages changed
if pages_changed:
    systemd.service(
        name="Restart web_server service",
        service="web_server",
        restarted=True,
        _sudo=True,
    )
