"""Robot arena simulation main entry point."""
import pygame
import sys
import math
import threading
import time
from pathlib import Path

# Add robot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from arena_simulation import ArenaSimulation
from robot import Robot
from status_panel import StatusPanel
from window_setup import create_display
from common.mqtt_behavior import connect as mqtt_connect


class SimulationState:
    """Shared state between rendering and physics threads."""
    def __init__(self):
        self.lock = threading.Lock()
        self.running = True
        self.dt = 1.0 / 60.0  # Physics time step

        # Mouse drag state
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.mouse_world_x = 0
        self.mouse_world_y = 0


def physics_loop(state: SimulationState, robot: Robot, arena_sim: ArenaSimulation):
    """Run physics simulation in separate thread at consistent rate.

    Args:
        state: Shared simulation state
        robot: Robot instance
        arena_sim: Arena simulation instance
    """
    physics_rate = 60  # Hz
    physics_dt = 1.0 / physics_rate

    while True:
        start_time = time.time()

        with state.lock:
            if not state.running:
                break

            # Handle mouse dragging
            if state.dragging:
                robot.body.position = (
                    state.mouse_world_x - state.drag_offset_x,
                    state.mouse_world_y - state.drag_offset_y
                )
                robot.body.velocity = (0, 0)
                robot.body.angular_velocity = 0

            # Apply motor velocities (before physics step)
            robot.apply_motor_velocities()

            # Step physics simulation
            arena_sim.step(physics_dt)

            # Update encoders based on actual motion (after physics step)
            robot.update_encoders(physics_dt)

            # Update distance sensor based on current position
            robot.update_distance_sensor(arena_sim)

        # Sleep to maintain consistent physics rate
        elapsed = time.time() - start_time
        sleep_time = physics_dt - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)


def main():
    """Run the simulation."""
    # Connect to MQTT broker
    print("Connecting to MQTT broker...")
    config_path = Path(__file__).parent / ".env.json"
    mqtt_client = mqtt_connect(config_path=str(config_path))

    # Initialize pygame
    pygame.init()

    # Create arena simulation (includes physics space)
    arena_sim = ArenaSimulation()

    # Create robot at random position with MQTT client
    robot = arena_sim.random_pose(Robot, mqtt_client)

    # Create status panel
    status_panel = StatusPanel(arena_sim.display_width, arena_sim.display_height)

    # Create display window (arena + status panel)
    total_width = arena_sim.display_width + StatusPanel.WIDTH
    screen = create_display(
        total_width,
        arena_sim.display_height,
        "Robot Arena Simulation"
    )

    # Create shared state
    state = SimulationState()

    # Start physics thread
    physics_thread = threading.Thread(
        target=physics_loop,
        args=(state, robot, arena_sim),
        daemon=True
    )
    physics_thread.start()

    # Clock for controlling rendering frame rate
    clock = pygame.time.Clock()

    # Main rendering and event loop
    while state.running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                with state.lock:
                    state.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    with state.lock:
                        state.running = False
                elif event.key == pygame.K_l:
                    # Log status snapshot to terminal
                    with state.lock:
                        status_panel.log_status_snapshot(robot, arena_sim)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Convert screen to world coordinates
                    mouse_x = (event.pos[0] - arena_sim.MARGIN) / arena_sim.SCALE
                    mouse_y = (arena_sim.display_height - event.pos[1] - arena_sim.MARGIN) / arena_sim.SCALE

                    with state.lock:
                        # Check if click is on robot
                        dx = mouse_x - robot.x
                        dy = mouse_y - robot.y
                        distance = math.sqrt(dx*dx + dy*dy)

                        # Use robot length as click radius
                        if distance < robot.LENGTH:
                            state.dragging = True
                            state.drag_offset_x = dx
                            state.drag_offset_y = dy

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    with state.lock:
                        state.dragging = False

            elif event.type == pygame.MOUSEWHEEL:
                with state.lock:
                    if state.dragging:
                        # Rotate robot by 10 degrees (pi/18 radians)
                        rotation_increment = math.pi / 18
                        robot.body.angle += event.y * rotation_increment
                        # Normalize angle to 0-2π range
                        robot.body.angle = robot.body.angle % (2 * math.pi)

        # Update mouse position for physics thread
        if state.dragging:
            mouse_pos = pygame.mouse.get_pos()
            # Convert screen to world coordinates
            with state.lock:
                state.mouse_world_x = (mouse_pos[0] - arena_sim.MARGIN) / arena_sim.SCALE
                state.mouse_world_y = (arena_sim.display_height - mouse_pos[1] - arena_sim.MARGIN) / arena_sim.SCALE

        # Render (with lock to ensure consistent state)
        with state.lock:
            # Draw arena (walls only)
            arena_sim.draw(screen)

            # Draw robot
            robot.draw(screen, arena_sim.world_to_screen)

            # Draw status panel
            status_panel.draw(screen, robot)

        # Update display
        pygame.display.flip()

        # Control rendering frame rate (can be different from physics rate)
        clock.tick(60)

    # Wait for physics thread to finish
    physics_thread.join(timeout=2.0)

    # Clean up
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
