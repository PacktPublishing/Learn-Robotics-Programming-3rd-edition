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
    BACKGROUND_COLOR = (240, 240, 240)
    WALL_COLOR = (0, 0, 0)
    WALL_THICKNESS = 3

    def __init__(self):
        """Initialize the arena simulation with pymunk space and rendering."""
        # Get dimensions directly from arena.py - single source of truth
        self.arena_width = arena.right
        self.arena_height = arena.top
        self.walls = arena.walls

        self.display_width = int(self.arena_width * self.SCALE)
        self.display_height = int(self.arena_height * self.SCALE)

        # Create pymunk physics space
        self.space = pymunk.Space()
        # No gravity for top-down 2D simulation
        self.space.gravity = (0, 0)

        # Add arena walls to physics space
        self._create_wall_bodies()

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

    def draw(self, screen: pygame.Surface):
        """Draw the arena on the pygame screen.

        Args:
            screen: Pygame surface to draw on
        """
        # Clear screen
        screen.fill(self.BACKGROUND_COLOR)

        # Convert wall coordinates to screen space
        screen_walls = [self.world_to_screen(x, y) for x, y in self.walls]

        # Draw walls
        pygame.draw.lines(screen, self.WALL_COLOR, True, screen_walls, self.WALL_THICKNESS)
