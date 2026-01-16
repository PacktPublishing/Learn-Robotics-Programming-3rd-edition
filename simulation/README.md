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

The simulations package setup is independent from the pyinfra setup, with python dependencies defined in simulation/pyproject.toml.

## Running the Simulation

The simulation consists of three components:
1. MQTT broker (mosquitto) - runs in Docker
2. Robot services (behavior_line, etc.) - run in Docker
3. Pygame visualization - runs on host with uv

### Setup

First, ensure you have the mosquitto password file created:
```bash
cd simulation
docker run --rm -v $(pwd)/mosquitto.passwd:/mosquitto/config/passwd eclipse-mosquitto:2 mosquitto_passwd -b /mosquitto/config/passwd sim-user sim-password
```

### Start the MQTT Broker

Start the broker in daemon mode (runs in background):
```bash
cd simulation
docker compose up mqtt
```

### Start the Pygame Simulation

Run the visualization on your host machine:
```bash
cd simulation
uv pip install --system .[external]
uv run ./simulation
```

Controls:
- Press ESC or Q to quit
- Close the window to exit

### Start Robot Services

Start robot behavior services (like behavior_line):
```bash
cd simulation
docker compose --profile robot-services up --build robot-behavior
```

Or run the fixed distance avoider demonstration:
```bash
cd simulation
docker compose --profile robot-services up --build fixed-distance-avoider
```

### Start Web Control Interface

Start the web control interface to visualize sensor data:
```bash
cd simulation
docker compose --profile web-interface up --build web-control
```

Then open your browser to http://localhost:8080 and navigate to the desired page (e.g., `fixed_distance_avoider.html`).

### Stop Everything

Stop all services:
```bash
cd simulation
docker compose --profile robot-services down
```

## Todo list

- The glitch rate, is this a constant of the simulation or the sensor? It probably makes sense for the sensor to have a glitch rate parameter, so we can test different rates. Light conditions in the real world could affect this.


## Styleing todo

We can make this interface look a bit more futuristic/cyberpunk. But that's for later.
