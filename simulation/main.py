"""Robot arena simulation main entry point."""
import logging
import pygame
import sys
import math
from pathlib import Path

# Add robot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from arena_simulation import ArenaSimulation
from robot import Robot
from window_setup import create_display
from common import arena
from common.mqtt_behavior import connect as mqtt_connect


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

    # Create robot at random position with MQTT client and add to physics space
    robot = Robot.random_pose(
        arena.right,
        arena.top,
        arena.cutout_left,
        arena.cutout_top,
        arena_sim.space,
        mqtt_client
    )

    # Create display window
    screen = create_display(
        arena_sim.display_width,
        arena_sim.display_height,
        "Robot Arena Simulation"
    )

    # Clock for controlling frame rate
    clock = pygame.time.Clock()
    dt = 1.0 / 60.0  # 60 FPS time step

    # Mouse drag state
    dragging = False
    drag_offset_x = 0
    drag_offset_y = 0

    # Main simulation loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Convert screen to world coordinates
                    mouse_x = event.pos[0] / arena_sim.SCALE
                    mouse_y = (arena_sim.display_height - event.pos[1]) / arena_sim.SCALE

                    # Check if click is on robot
                    dx = mouse_x - robot.x
                    dy = mouse_y - robot.y
                    distance = math.sqrt(dx*dx + dy*dy)

                    # Use robot length as click radius
                    if distance < robot.LENGTH:
                        dragging = True
                        drag_offset_x = dx
                        drag_offset_y = dy

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click release
                    dragging = False

            elif event.type == pygame.MOUSEWHEEL:
                if dragging:
                    # Rotate robot by 10 degrees (pi/18 radians)
                    rotation_increment = math.pi / 18
                    robot.body.angle += event.y * rotation_increment

        # Handle mouse dragging
        if dragging:
            mouse_pos = pygame.mouse.get_pos()
            # Convert screen to world coordinates
            world_x = mouse_pos[0] / arena_sim.SCALE
            world_y = (arena_sim.display_height - mouse_pos[1]) / arena_sim.SCALE

            # Update robot position (subtract offset to maintain grab point)
            robot.body.position = (
                world_x - drag_offset_x,
                world_y - drag_offset_y
            )
            # Reset velocity when manually positioning
            robot.body.velocity = (0, 0)
            robot.body.angular_velocity = 0

        # Apply motor velocities (before physics step)
        robot.apply_motor_velocities()

        # Step physics simulation
        arena_sim.step(dt)

        # Update encoders based on actual motion (after physics step)
        robot.update_encoders(dt)

        # Draw arena (including status panel)
        arena_sim.draw(screen, robot)

        # Draw robot
        robot.draw(screen, arena_sim.world_to_screen)

        # Update display
        pygame.display.flip()

        # Control frame rate (60 FPS)
        clock.tick(60)

    # Clean up
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
