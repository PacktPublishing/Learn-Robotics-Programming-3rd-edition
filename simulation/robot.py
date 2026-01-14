"""Robot sprite for the simulation."""
import pygame
import pymunk
import random
import math
import time
import ujson as json

from common.mqtt_behavior import publish_json


class RobotWheel:
    """Simulates a robot wheel with motor and encoder characteristics."""

    # Motor speed calibration
    BASE_SPEED_MM_PER_SEC = 195.0  # Mean speed at motor setting 1.0
    SPEED_VARIATION_STDDEV = 5.0   # Standard deviation for motor variation

    # Encoder settings (matching inventor_hat_service.py)
    COUNTS_PER_REV = 32 * 120  # sensor poles * gear ratio
    WHEEL_DIAMETER = 67  # mm
    WHEEL_RADIUS = WHEEL_DIAMETER / 2  # mm

    def __init__(self):
        """Initialize wheel with random speed variation and encoder."""
        # Add random variation to simulate real motor/gear/wheel differences
        self.speed_factor = random.gauss(
            1.0,
            self.SPEED_VARIATION_STDDEV / self.BASE_SPEED_MM_PER_SEC
        )
        self.current_speed = 0.0  # Current motor speed setting (-1.0 to 1.0)

        # Encoder state
        self.encoder_count = 0.0  # Accumulated encoder counts
        self.encoder_radians = 0.0  # Accumulated radians
        self.last_update_time = time.time()

    def set_speed(self, speed: float):
        """Set the wheel motor speed.

        Args:
            speed: Motor speed from -1.0 (full reverse) to 1.0 (full forward)
        """
        self.current_speed = max(-1.0, min(1.0, speed))

    def get_velocity(self) -> float:
        """Get the current wheel velocity in mm/s.

        Returns:
            Velocity in mm/s
        """
        return self.current_speed * self.BASE_SPEED_MM_PER_SEC * self.speed_factor

    def update_encoder(self, dt: float):
        """Update encoder counts based on wheel movement.

        Args:
            dt: Time step in seconds
        """
        # Calculate distance traveled in mm
        velocity = self.get_velocity()
        distance_mm = velocity * dt

        # Convert to radians of wheel rotation
        radians = distance_mm / self.WHEEL_RADIUS

        # Update accumulated values
        self.encoder_radians += radians

        # Convert radians to encoder counts
        counts_per_radian = self.COUNTS_PER_REV / (2 * math.pi)
        self.encoder_count = self.encoder_radians * counts_per_radian

    def reset_encoder(self):
        """Reset encoder to zero."""
        self.encoder_count = 0.0
        self.encoder_radians = 0.0

    def get_encoder_data(self):
        """Get encoder data in the format expected by behaviors.

        Returns:
            dict: Dictionary with distance and velocity data
        """
        velocity = self.get_velocity()

        return {
            "distance": self.encoder_radians * self.WHEEL_RADIUS,  # mm
            "mm_per_sec": velocity  # mm/s
        }

class Robot:
    """Represents the robot in the simulation."""

    # Robot dimensions (in mm) - approximate size of the robot
    WIDTH = 125
    LENGTH = 200
    WHEEL_DIAMETER = 67
    WHEEL_POSITION_FROM_FRONT = 100
    WHEEL_THICKNESS = 25
    WHEEL_SEPARATION = WIDTH  # Distance between left and right wheels

    # Physics properties
    MASS = 1.0  # kg
    MOMENT_SCALE = 1.0  # Scale factor for moment of inertia

    # Motor timeout
    MOTOR_TIMEOUT = 1.0  # Stop motors after 1 second of no commands

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

        # Create motor wheels with individual characteristics
        self.left_wheel = RobotWheel()
        self.right_wheel = RobotWheel()

        # Track last motor command time for timeout
        self.last_motor_command_time = 0.0

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

        # Subscribe to motor control messages if MQTT client available
        if self.mqtt_client:
            self.mqtt_client.subscribe("motors/wheels")
            self.mqtt_client.message_callback_add(
                "motors/wheels", self._on_motor_command
            )
            self.mqtt_client.subscribe("sensors/encoders/control/reset")
            self.mqtt_client.message_callback_add(
                "sensors/encoders/control/reset", self._on_encoder_reset
            )

        # Encoder update timing
        self.last_encoder_publish = time.time()
        self.encoder_publish_interval = 0.1  # Publish at 10 Hz like real robot

    def _on_encoder_reset(self, client, userdata, message):
        """Handle encoder reset MQTT messages.

        Args:
            client: MQTT client
            userdata: User data
            message: MQTT message
        """
        self.left_wheel.reset_encoder()
        self.right_wheel.reset_encoder()

    def _on_motor_command(self, client, userdata, message):
        """Handle motor/wheels MQTT messages.

        Args:
            client: MQTT client
            userdata: User data
            message: MQTT message with [left_speed, right_speed] payload
        """
        speeds = json.loads(message.payload)
        if len(speeds) >= 2:
            self.left_wheel.set_speed(speeds[0])
            self.right_wheel.set_speed(speeds[1])
            self.last_motor_command_time = time.time()

    def update_motors(self, dt: float):
        """Apply motor forces to the robot body based on wheel speeds.

        Args:
            dt: Time step in seconds
        """
        # Check for motor command timeout
        if self.last_motor_command_time > 0:
            time_since_last_command = time.time() - self.last_motor_command_time
            if time_since_last_command > self.MOTOR_TIMEOUT:
                # Stop motors after timeout
                self.left_wheel.set_speed(0.0)
                self.right_wheel.set_speed(0.0)

        # Update wheel encoders
        self.left_wheel.update_encoder(dt)
        self.right_wheel.update_encoder(dt)

        # Publish encoder data at regular intervals
        current_time = time.time()
        if current_time - self.last_encoder_publish >= self.encoder_publish_interval:
            self._publish_encoder_data()
            self.last_encoder_publish = current_time

        # Get wheel velocities in mm/s
        left_velocity = self.left_wheel.get_velocity()
        right_velocity = self.right_wheel.get_velocity()

        # Calculate differential drive kinematics
        # Linear velocity (forward) is average of both wheels
        linear_velocity = (left_velocity + right_velocity) / 2.0

        # Angular velocity from difference between wheels
        # omega = (v_right - v_left) / wheel_separation
        angular_velocity = (right_velocity - left_velocity) / self.WHEEL_SEPARATION

        # Convert to robot's local frame and apply
        angle = self.body.angle
        vx = linear_velocity * math.cos(angle)
        vy = linear_velocity * math.sin(angle)

        # Set velocities directly (simpler than forces for this use case)
        self.body.velocity = (vx, vy)
        self.body.angular_velocity = angular_velocity

    def _publish_encoder_data(self):
        """Publish encoder data to MQTT."""
        if not self.mqtt_client:
            return

        left_data = self.left_wheel.get_encoder_data()
        right_data = self.right_wheel.get_encoder_data()

        publish_json(
            self.mqtt_client,
            "sensors/encoders/data",
            {
                "left_distance": left_data["distance"],
                "right_distance": right_data["distance"],
                "left_mm_per_sec": left_data["mm_per_sec"],
                "right_mm_per_sec": right_data["mm_per_sec"],
            }
        )

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
