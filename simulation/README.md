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

- We don't need the "space" for a robot to be optional, I think we always will have one in the simulation. - done
- The next sensor I want to add is a distance sensor. - done
- The robot has an VL53l5cx in the 8x8 array mode. Please check datasheets - done
- This probably belongs in its own simulated vl53l5cx class and python module, imported and used by the main robot class. - done
- The sensor is mounted on the front of the robot, in the middle, approximatly 5mm in from the front. This should be constants in the robot class. - done
- Use the sensor datasheet to determine the field of view, and range. - done
- Note that there are occasional glitches - the "3000's" for incorrect readings. Have an adjustable rate for setting this so we can test the robot code's handling of glitches. - done
- 4 rows detecting a floor (A constant for now in the sensor object), the other rows would be detecting what is in front of the robot. - done
- The top 4 rows can use raycasting to determine the distance to obstacles in front of them. - done
- I think we may need a bit of threading or multiprocessing here - the simulation is taking a while to launch, and tear down. Mainly to decouple the pygame event/rendering loop from the physics simulation loop. - done
- We can store the height in a robot constant for now, since the simulation is 2d, however, if this is passed in when initialising the sensor object, we cna use that to calculate (using the field of view) how many floor rows it should register - or what they should look like. It is mounted so the sensor element is about 45 mm above the floor. - done
- Consult robot/distance_sensor_service.py for the MQTT topics, data format and behavior (start/stop ranging) - done
- The sensors don't yet seem right - I'm not seeing the right data for the top rows
  - We want some debug, probably in the status panel.



Since we are in 2d, the simulation can provide the following data:
- When the robot is updated, it should pass in its current position and orientation to the distance sensor object for it to calculate the distances.
- The floor detection - if it's 45 mm above the floor, then based on the field of view, therefor the projection angle from each sensor, we can calculate the distance to the floor for each of the bottom 4 rows - this sounds like pythagoras theorem.
- The glitch rate, is this a constant of the simulation or the sensor? It probably makes sense for the sensor to have a glitch rate parameter, so we can test different rates. Light conditions in the real world could affect this.
- It might be nice to have 3 or 4 pixels of margin around the rendered map and robot in pygame, so we can see the boundaries better.
- We need a docker compose entry point to run one of the distance sensor demonstration scripts, to show the sensor working in the simulation.

## Debug

So I used the page distance plotter, and it looks like we are getting the four lower rows, but I was expecting the upper rows to show something. Perhaps we can start the simulation, run an mqtt sub in a terminal, and see what values we are getting? I can move the robot to a few positions so we can see the result.
It might be good to have the robot position displayed in the status too.

## Styleing todo

We can make this interface look a bit more futuristic/cyberpunk. But that's for later.
