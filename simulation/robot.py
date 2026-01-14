"""Robot sprite for the simulation."""
import pygame
import pymunk
import random
import math


class Robot:
    """Represents the robot in the simulation."""

    # Robot dimensions (in mm) - approximate size of the robot
    WIDTH = 125
    LENGTH = 200
    WHEEL_DIAMETER = 67
    WHEEL_POSITION_FROM_FRONT = 100
    WHEEL_THICKNESS = 25

    # Physics properties
    MASS = 1.0  # kg
    MOMENT_SCALE = 1.0  # Scale factor for moment of inertia

    # Display settings
    ROBOT_COLOR = (50, 100, 200)  # Blue
    WHEEL_COLOR = (40, 40, 40)  # Dark gray

    def __init__(self, x: float, y: float, angle: float = 0.0, space: pymunk.Space = None, mqtt_client=None):
        """Initialize the robot with a pymunk rigid body.

        Args:
            x: X position in mm
            y: Y position in mm
            angle: Orientation angle in radians (0 is facing right/east)
            space: Pymunk space to add the robot body to
            mqtt_client: Optional MQTT client for communication
        """
        self.mqtt_client = mqtt_client

        # Create pymunk body
        moment = pymunk.moment_for_box(self.MASS, (self.LENGTH, self.WIDTH)) * self.MOMENT_SCALE
        self.body = pymunk.Body(self.MASS, moment)
        self.body.position = (x, y)
        self.body.angle = angle

        # Create shape for the robot body
        half_length = self.LENGTH / 2
        half_width = self.WIDTH / 2
        vertices = [
            (-half_length, -half_width),
            (half_length, -half_width),
            (half_length, half_width),
            (-half_length, half_width)
        ]
        self.shape = pymunk.Poly(self.body, vertices)
        self.shape.friction = 0.7
        self.shape.elasticity = 0.1

        # Add to space if provided
        if space:
            space.add(self.body, self.shape)

    @property
    def x(self) -> float:
        """Get robot X position from body."""
        return self.body.position.x

    @property
    def y(self) -> float:
        """Get robot Y position from body."""
        return self.body.position.y

    @property
    def angle(self) -> float:
        """Get robot angle from body."""
        return self.body.angle

    @classmethod
    def random_pose(cls, arena_width: float, arena_height: float,
                   cutout_left: float, cutout_top: float, space: pymunk.Space = None, mqtt_client=None) -> 'Robot':
        """Create a robot at a random valid position in the arena.

        Args:
            arena_width: Width of the arena in mm
            arena_height: Height of the arena in mm
            cutout_left: X coordinate of the cutout
            cutout_top: Y coordinate of the cutout
            space: Pymunk space to add the robot body to
            mqtt_client: Optional MQTT client for communication

        Returns:
            Robot instance at a random valid position
        """
        margin = max(cls.WIDTH, cls.LENGTH)

        # Choose a random position, avoiding the cutout area
        while True:
            x = random.uniform(margin, arena_width - margin)
            y = random.uniform(margin, arena_height - margin)

            # Check if position is in the valid arena (not in cutout)
            if x >= cutout_left and y < cutout_top:
                continue  # In the cutout area, try again
            break

        angle = random.uniform(0, 2 * math.pi)
        return cls(x, y, angle, space, mqtt_client)

    def draw(self, screen: pygame.Surface, world_to_screen_fn):
        """Draw the robot on the screen using body state.

        Args:
            screen: Pygame surface to draw on
            world_to_screen_fn: Function to convert world coords to screen coords
        """
        # Get position and angle from physics body
        x = self.body.position.x
        y = self.body.position.y
        angle = self.body.angle

        # Calculate the four corners of the robot rectangle
        # Robot is centered at (x, y)
        half_width = self.WIDTH / 2
        half_length = self.LENGTH / 2

        # Local coordinates (before rotation)
        corners = [
            (-half_length, -half_width),  # Back left
            (half_length, -half_width),   # Front left
            (half_length, half_width),    # Front right
            (-half_length, half_width)    # Back right
        ]

        # Rotate and translate corners to world coordinates
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        world_corners = []
        for lx, ly in corners:
            # Rotate
            wx = lx * cos_a - ly * sin_a + x
            wy = lx * sin_a + ly * cos_a + y
            world_corners.append((wx, wy))

        # Convert to screen coordinates
        screen_corners = [world_to_screen_fn(wx, wy) for wx, wy in world_corners]

        # Draw the robot
        pygame.draw.polygon(screen, self.ROBOT_COLOR, screen_corners)

        # Draw wheels
        self._draw_wheels(screen, world_to_screen_fn, x, y, cos_a, sin_a)

        # Draw a line to indicate front direction
        front_x = x + (half_length + 20) * cos_a
        front_y = y + (half_length + 20) * sin_a

        center_screen = world_to_screen_fn(x, y)
        front_screen = world_to_screen_fn(front_x, front_y)

        pygame.draw.line(screen, (255, 0, 0), center_screen, front_screen, 2)

    def _draw_wheels(self, screen: pygame.Surface, world_to_screen_fn, x: float, y: float, cos_a: float, sin_a: float):
        """Draw the left and right wheels.

        Args:
            screen: Pygame surface to draw on
            world_to_screen_fn: Function to convert world coords to screen coords
            x: Robot X position
            y: Robot Y position
            cos_a: Cosine of robot angle
            sin_a: Sine of robot angle
        """
        # Wheel position (distance from center to wheel centers)
        wheel_offset_x = self.LENGTH / 2 - self.WHEEL_POSITION_FROM_FRONT
        wheel_offset_y = self.WIDTH / 2 + self.WHEEL_THICKNESS / 2

        half_wheel_diameter = self.WHEEL_DIAMETER / 2
        half_wheel_thickness = self.WHEEL_THICKNESS / 2

        # Left and right wheel positions in local coordinates
        for side in [-1, 1]:  # -1 for left, 1 for right
            # Wheel center in local coordinates
            local_wheel_x = -wheel_offset_x
            local_wheel_y = side * wheel_offset_y

            # Wheel corners in local coordinates (relative to wheel center)
            wheel_corners = [
                (local_wheel_x - half_wheel_diameter, local_wheel_y - half_wheel_thickness),
                (local_wheel_x + half_wheel_diameter, local_wheel_y - half_wheel_thickness),
                (local_wheel_x + half_wheel_diameter, local_wheel_y + half_wheel_thickness),
                (local_wheel_x - half_wheel_diameter, local_wheel_y + half_wheel_thickness),
            ]

            # Rotate and translate to world coordinates
            world_wheel_corners = []
            for lx, ly in wheel_corners:
                wx = lx * cos_a - ly * sin_a + x
                wy = lx * sin_a + ly * cos_a + y
                world_wheel_corners.append((wx, wy))

            # Convert to screen coordinates
            screen_wheel_corners = [world_to_screen_fn(wx, wy) for wx, wy in world_wheel_corners]

            # Draw the wheel
            pygame.draw.polygon(screen, self.WHEEL_COLOR, screen_wheel_corners)
