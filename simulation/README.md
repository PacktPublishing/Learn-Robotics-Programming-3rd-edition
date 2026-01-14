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

UV will be used to manage dependencies.
A container will be built, using the robot services, and robot control code as a base, with key services (close to hardware) removed, so the simulation can interact directly.

The robot control environment will be in robot.Dockerfile.
The simulation would be run with `uv run ./simulation` from the simulation directory. The simulation runs in foreground with pygame, so would not be daemonized.

Controls:
- Press ESC or Q to quit
- Close the window to exit

## Todo list

- Let's add a simple robot sprite - start with a rectangle for now - we can then add the wheel contact points relative to that rectangle. (parameters for width, length, wheelbase, etc, and the castor point too).
