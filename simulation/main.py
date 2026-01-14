"""Robot arena simulation main entry point."""
import pygame
import sys
from pathlib import Path

# Add robot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from arena_simulation import ArenaSimulation
from robot import Robot
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
    screen = pygame.display.set_mode((arena_sim.display_width, arena_sim.display_height))
    pygame.display.set_caption("Robot Arena Simulation")

    # Clock for controlling frame rate
    clock = pygame.time.Clock()
    dt = 1.0 / 60.0  # 60 FPS time step

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

        # Step physics simulation
        arena_sim.step(dt)

        # Update robot motors
        robot.update_motors(dt)

        # Draw arena
        arena_sim.draw(screen)

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
