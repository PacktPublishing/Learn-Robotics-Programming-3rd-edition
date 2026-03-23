"""Arena simulation with physics using pygame and pymunk."""
import math
import pygame
import pymunk
import random
import sys
from pathlib import Path
from typing import Tuple

# Add robot directory to path so imports relative to robot/ work
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "robot"))

from common import arena


class ArenaSimulation:
    """Manages the arena physics simulation and rendering using pymunk and pygame."""

    # Display settings
    SCALE = 0.4  # Scale factor for display (mm to pixels)
    MARGIN = 4  # Margin around arena in pixels
    ARENA_PADDING = 8  # Padding inside the arena border (pixels)
    BACKGROUND_COLOR = (0, 0, 0)  # Black background
    ARENA_FILL_COLOR = (5, 10, 15)  # Very faint blue fill
    WALL_COLOR = (0, 191, 255)  # Electric blue (matching status panel)
    WALL_THICKNESS = 2

    # Arena shear (dimensionless). Set small values to simulate non-rectilinear
    # construction. Shear is applied as:
    # [x']   [1  SHEAR_X] [x]
    # [y'] = [SHEAR_Y 1]  [y]
    ARENA_SHEAR_X = 0.001  # x' = x + SHEAR_X * y
    ARENA_SHEAR_Y = 0.0  # y' = y + SHEAR_Y * x

    def __init__(self):
        """Initialize the arena simulation with pymunk space and rendering."""
        # Get dimensions directly from arena.py - single source of truth
        self.arena_width = arena.right
        self.arena_height = arena.top
        self.walls = arena.walls
        # Distorted arena outline used for physics + rendering only.
        self.sheared_walls = [self._apply_arena_shear(point) for point in self.walls]

        self.display_width = int(self.arena_width * self.SCALE) + (self.MARGIN * 2) + (self.ARENA_PADDING * 2)
        self.display_height = int(self.arena_height * self.SCALE) + (self.MARGIN * 2) + (self.ARENA_PADDING * 2)

        # Create pymunk physics space
        self.space = pymunk.Space()
        # No gravity for top-down 2D simulation
        self.space.gravity = (0, 0)
        # Add damping to simulate friction and air resistance
        self.space.damping = 0.95  # 0 = no damping, 1 = infinite damping

        # Add arena walls to physics space
        self._create_wall_bodies()

        # Initialize font for status display
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

    def random_pose(self, robot_class, mqtt_client=None):
        """Create a robot at a random valid position in the arena.

        Args:
            robot_class: Robot class to instantiate
            mqtt_client: Optional MQTT client for communication

        Returns:
            Robot instance at a random valid position
        """
        robot_config = getattr(robot_class, "CONFIG", robot_class)
        margin = max(robot_config.WIDTH, robot_config.LENGTH)

        # Choose a random position, avoiding the cutout area
        while True:
            x = random.uniform(margin, self.arena_width - margin)
            y = random.uniform(margin, self.arena_height - margin)

            # Check if position is in the valid arena (not in cutout)
            # Cutout is at top-right corner
            if x >= arena.cutout_left and y >= arena.cutout_top:
                continue  # In the cutout area, try again
            break

        angle = random.uniform(0, 2 * math.pi)
        return robot_class(x, y, angle, self.space, mqtt_client)

    def _create_wall_bodies(self):
        """Create static wall bodies in the physics space."""
        # Create static body for walls (doesn't move)
        static_body = self.space.static_body

        # Create segments for each wall section
        for i in range(len(self.sheared_walls)):
            start = self.sheared_walls[i]
            end = self.sheared_walls[(i + 1) % len(self.sheared_walls)]

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
        screen_x = int(x * self.SCALE) + self.MARGIN + self.ARENA_PADDING
        # Flip Y axis (screen Y=0 is at top, world Y=0 is at bottom)
        screen_y = int(self.display_height - (y * self.SCALE)) - self.MARGIN - self.ARENA_PADDING
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
        screen_walls = [self.world_to_screen(x, y) for x, y in self.sheared_walls]

        # Draw arena fill
        pygame.draw.polygon(screen, self.ARENA_FILL_COLOR, screen_walls)

        # Draw walls
        pygame.draw.lines(screen, self.WALL_COLOR, True, screen_walls,
                         self.WALL_THICKNESS)

    def _apply_arena_shear(self, point: Tuple[float, float]) -> Tuple[float, float]:
        """Apply a small shear to arena coordinates to simulate construction error."""
        x, y = point
        sheared_x = x + (self.ARENA_SHEAR_X * y)
        sheared_y = y + (self.ARENA_SHEAR_Y * x)
        return (sheared_x, sheared_y)
