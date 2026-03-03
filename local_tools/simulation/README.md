# Simulation

## Purpose

This will be a simulation environment for the arena and robot used in the book.
It uses Pyagme to display in 2D, and PyBullet to simulate physics.

## Architecture

The simulation will have MQTT listeners, and will publish sensor data
just like the real robot. This will allow the same control code to be used
with either the real robot or the simulated robot.

We will target the distance sensors, motor control and encoder data.
The simulation display will be the "robot position" according to the simulation.

The simulation uses data from robot/common/arena.py to define the arena layout - a single pointof truth, and helpers from robot/common/mqtt_behaviors.py to manage MQTT interactions.

Local tools share a single uv project with dependencies defined in local_tools/pyproject.toml.

## Running the Simulation

The simulation consists of three components:
1. MQTT broker (mosquitto) - runs in Docker
2. Robot services (behavior_line, etc.) - run in Docker
3. Pygame visualization - runs on host with uv

### One-command startup

Start everything in one terminal:

```bash
cd local_tools/simulation
./start_simulation.sh
```

This starts MQTT, pygame simulation, web control, and robot services.
Press Ctrl+C to stop only the pygame process. Docker services continue to run.

### Setup

You will need either Docker Desktop or Podman with compose support.

First, ensure you have the mosquitto password file created:
```bash
cd local_tools/simulation
docker run --rm -v $(pwd)/mosquitto.passwd:/mosquitto/config/passwd eclipse-mosquitto:2 mosquitto_passwd -b /mosquitto/config/passwd sim-user sim-password
```

### Start the MQTT Broker

Start the broker in daemon mode (runs in background):
```bash
cd local_tools/simulation
docker compose up mqtt
```

### Start the Pygame Simulation

Run the visualization on your host machine:

```bash
cd local_tools/simulation
uv sync --project .. --extra simulation
uv run --project .. python simulation.py
```

This uses uv's project virtual environment and does not install into your system Python.
Use `uv run --project .. python simulation.py` to avoid path resolution differences between shells.

If VS Code auto-activates a different environment, uv may warn that `VIRTUAL_ENV`
is being ignored; that warning is safe, and uv will still use `.venv` for this project.

### Systematic asymmetry tuning

You can inject persistent left/right asymmetry via environment variables:

- `SIM_LEFT_DRIVE_SCALE` (default `1.0`)
- `SIM_RIGHT_DRIVE_SCALE` (default `1.0`)
- `SIM_LEFT_ENCODER_SCALE` (default `1.0`)
- `SIM_RIGHT_ENCODER_SCALE` (default `1.0`)

Examples:

```bash
cd local_tools/simulation
SIM_LEFT_DRIVE_SCALE=0.96 SIM_RIGHT_DRIVE_SCALE=1.02 uv run --project .. python main.py
```

```bash
cd local_tools/simulation
SIM_LEFT_ENCODER_SCALE=1.00 SIM_RIGHT_ENCODER_SCALE=0.98 uv run --project .. python main.py
```

`*_DRIVE_SCALE` affects how wheel commands move the body (traction/weight-bias style asymmetry).
`*_ENCODER_SCALE` affects reported encoder distance relative to motion (calibration mismatch).

Controls:
- Press ESC or Q to quit
- Close the window to exit

### Start Robot Services

Start the robot services container which runs supervisord with:
- launcher_service: Allows MQTT control of behaviors
- wheel_control_service: PID speed controller (same as real robot)
- config_store: Configuration storage service

Note: Hardware services (inventor_hat, distance_sensor) are replaced by the pygame simulation.

```bash
cd local_tools/simulation
docker compose --profile robot-services up --build robot-services
```

Now you can use the launcher service via MQTT to start/stop behaviors:
```bash
# Start the fixed distance avoider
mosquitto_pub -h localhost -t launcher/start -m "fixed_distance_avoider"

# Stop it
mosquitto_pub -h localhost -t launcher/stop -m "fixed_distance_avoider"
```

Available behaviors:
- `behavior_line`
- `behavior_path`
- `fixed_distance_avoider`
- `smooth_distance_avoider`
- `drive_known_distance`
- `circle_head_behavior`
- `localisation`

#### Updating Robot Code

The robot code is mounted as a volume, so you can edit files and restart without rebuilding:

```bash
# After editing robot code, restart the container
docker compose restart robot-services

# Or restart a specific behavior via supervisorctl
docker compose exec robot-services supervisorctl restart fixed_distance_avoider
```

### Start Web Control Interface

Start the web control interface to visualize sensor data:
```bash
cd local_tools/simulation
docker compose --profile web-interface up --build web-control
```

Then open your browser to http://localhost:8080 and navigate to the desired page (e.g., `fixed_distance_avoider.html`).

### WSL troubleshooting

If the pygame app appears in the Windows taskbar but the window does not show,
WSLg may be in a bad state.

Quick recovery on Windows:

```bash
wsl --shutdown
```

Then restart Docker Desktop / VS Code and run the simulation again.

### Stop Everything

Stop all services:
```bash
cd local_tools/simulation
docker compose --profile robot-services down
```

## Todo list

- The glitch rate, is this a constant of the simulation or the sensor? It probably makes sense for the sensor to have a glitch rate parameter, so we can test different rates. Light conditions in the real world could affect this.


## Test notes

I've compared the vl53l5cx distance sensor array orientation with teh sensor arrya on the robot, and the orientation is correct.
