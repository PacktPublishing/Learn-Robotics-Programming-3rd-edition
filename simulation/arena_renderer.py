"""Arena renderer for the robot simulation using pygame."""
import pygame
import sys
from pathlib import Path
from typing import Tuple

# Add robot directory to path so imports relative to robot/ work
sys.path.insert(0, str(Path(__file__).parent.parent / "robot"))

from common import arena


class ArenaRenderer:
    """Renders the arena walls using pygame."""

    # Display settings
    SCALE = 0.4  # Scale factor for display (mm to pixels)
    BACKGROUND_COLOR = (240, 240, 240)
    WALL_COLOR = (0, 0, 0)
    WALL_THICKNESS = 3

    def __init__(self):
        """Initialize the arena renderer."""
        # Get dimensions directly from arena.py - single source of truth
        self.arena_width = arena.right
        self.arena_height = arena.top
        self.walls = arena.walls

        self.display_width = int(self.arena_width * self.SCALE)
        self.display_height = int(self.arena_height * self.SCALE)

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
