"""Arena simulation with physics using pygame and pymunk."""
import pygame
import pymunk
import sys
from pathlib import Path
from typing import Tuple

# Add robot directory to path so imports relative to robot/ work
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from common import arena


class ArenaSimulation:
    """Manages the arena physics simulation and rendering using pymunk and pygame."""

    # Display settings
    SCALE = 0.4  # Scale factor for display (mm to pixels)
    STATUS_PANEL_WIDTH = 250  # Width of status panel in pixels
    BACKGROUND_COLOR = (240, 240, 240)
    WALL_COLOR = (0, 0, 0)
    WALL_THICKNESS = 3
    STATUS_BG_COLOR = (220, 220, 220)
    STATUS_TEXT_COLOR = (0, 0, 0)

    def __init__(self):
        """Initialize the arena simulation with pymunk space and rendering."""
        # Get dimensions directly from arena.py - single source of truth
        self.arena_width = arena.right
        self.arena_height = arena.top
        self.walls = arena.walls

        self.arena_display_width = int(self.arena_width * self.SCALE)
        self.display_width = self.arena_display_width + self.STATUS_PANEL_WIDTH
        self.display_height = int(self.arena_height * self.SCALE)

        # Create pymunk physics space
        self.space = pymunk.Space()
        # No gravity for top-down 2D simulation
        self.space.gravity = (0, 0)

        # Add arena walls to physics space
        self._create_wall_bodies()

        # Initialize font for status display
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

    def _create_wall_bodies(self):
        """Create static wall bodies in the physics space."""
        # Create static body for walls (doesn't move)
        static_body = self.space.static_body

        # Create segments for each wall section
        for i in range(len(self.walls)):
            start = self.walls[i]
            end = self.walls[(i + 1) % len(self.walls)]

            wall_segment = pymunk.Segment(static_body, start, end, 2)
            wall_segment.elasticity = 0.8  # Some bounce
            wall_segment.friction = 0.5
            self.space.add(wall_segment)

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates (mm) to screen coordinates (pixels).

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm (0 at bottom, increases upward)

        Returns:
            Tuple of (screen_x, screen_y) in pixels
        """
        screen_x = int(x * self.SCALE)
        # Flip Y axis (screen Y=0 is at top, world Y=0 is at bottom)
        screen_y = int(self.display_height - (y * self.SCALE))
        return (screen_x, screen_y)

    def step(self, dt: float):
        """Step the physics simulation forward.

        Args:
            dt: Time step in seconds
        """
        self.space.step(dt)

    def draw(self, screen: pygame.Surface, robot=None):
        """Draw the arena on the pygame screen.

        Args:
            screen: Pygame surface to draw on
            robot: Optional robot instance to display status for
        """
        # Clear screen
        screen.fill(self.BACKGROUND_COLOR)

        # Convert wall coordinates to screen space
        screen_walls = [self.world_to_screen(x, y) for x, y in self.walls]

        # Draw walls
        pygame.draw.lines(screen, self.WALL_COLOR, True, screen_walls,
                         self.WALL_THICKNESS)

        # Draw status panel
        if robot:
            self._draw_status_panel(screen, robot)

    def _draw_status_panel(self, screen: pygame.Surface, robot):
        """Draw status information panel.

        Args:
            screen: Pygame surface to draw on
            robot: Robot instance to display status for
        """
        # Draw status panel background
        panel_rect = pygame.Rect(
            self.arena_display_width, 0,
            self.STATUS_PANEL_WIDTH, self.display_height
        )
        pygame.draw.rect(screen, self.STATUS_BG_COLOR, panel_rect)
        pygame.draw.line(
            screen, self.WALL_COLOR,
            (self.arena_display_width, 0),
            (self.arena_display_width, self.display_height),
            2
        )

        # Status text starting position
        x_offset = self.arena_display_width + 10
        y_offset = 20
        line_height = 30

        # Display encoder counts
        left_data = robot.left_wheel.get_encoder_data()
        right_data = robot.right_wheel.get_encoder_data()

        status_lines = [
            "ENCODER STATUS",
            "",
            f"Left Count:",
            f"  {robot.left_wheel.encoder_count:.1f}",
            f"Left Distance:",
            f"  {left_data['distance']:.1f} mm",
            "",
            f"Right Count:",
            f"  {robot.right_wheel.encoder_count:.1f}",
            f"Right Distance:",
            f"  {right_data['distance']:.1f} mm",
            "",
            f"Motor Speeds:",
            f"  L: {robot.left_wheel.current_speed:.2f}",
            f"  R: {robot.right_wheel.current_speed:.2f}",
        ]

        for i, line in enumerate(status_lines):
            text_surface = self.font.render(line, True, self.STATUS_TEXT_COLOR)
            screen.blit(text_surface, (x_offset, y_offset + i * line_height))
