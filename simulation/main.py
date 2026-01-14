"""Robot arena simulation main entry point."""
import pygame
import sys
from pathlib import Path

# Add robot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from arena_renderer import ArenaRenderer
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

    # Create arena renderer
    arena_renderer = ArenaRenderer()

    # Create robot at random position with MQTT client
    robot = Robot.random_pose(
        arena.right,
        arena.top,
        arena.cutout_left,
        arena.cutout_top,
        mqtt_client
    )

    # Create display window
    screen = pygame.display.set_mode((arena_renderer.display_width, arena_renderer.display_height))
    pygame.display.set_caption("Robot Arena Simulation")

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

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

        # Draw arena
        arena_renderer.draw(screen)

        # Draw robot
        robot.draw(screen, arena_renderer.world_to_screen)

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
