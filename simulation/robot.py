"""Robot sprite for the simulation."""
import pygame
import pymunk
import random
import math
import time
import ujson as json

from common.mqtt_behavior import publish_json
from simulated_vl53l5cx import SimulatedVL53L5CX


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

    def update_encoder(self, dt: float, actual_velocity: float = None):
        """Update encoder counts based on wheel movement.

        Args:
            dt: Time step in seconds
            actual_velocity: Actual wheel velocity in mm/s (from physics).
                           If None, uses commanded velocity.
        """
        # Use actual velocity from physics if provided, otherwise use commanded
        velocity = actual_velocity if actual_velocity is not None else self.get_velocity()

        # Apply velocity threshold to simulate static friction and mechanical play
        # Real encoders won't register movement below a minimum threshold
        VELOCITY_THRESHOLD = 1.0  # mm/s - minimum velocity to register movement
        if abs(velocity) < VELOCITY_THRESHOLD:
            velocity = 0.0

        # Calculate distance traveled in mm
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

    # Distance sensor mounting (VL53L5CX)
    DISTANCE_SENSOR_OFFSET_FROM_FRONT = 5  # mm - sensor is 5mm from front edge
    DISTANCE_SENSOR_HEIGHT = 45  # mm - sensor height above floor

    # Display settings
    ROBOT_COLOR = (50, 100, 200)  # Blue
    WHEEL_COLOR = (40, 40, 40)  # Dark gray

    def __init__(self, x: float, y: float, angle: float, space: pymunk.Space, mqtt_client=None):
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

        # Create shape for the robot body including wheel protrusions
        # Wheels extend WHEEL_THICKNESS/2 beyond the body on each side
        half_length = self.LENGTH / 2
        half_width = self.WIDTH / 2
        wheel_protrusion = self.WHEEL_THICKNESS / 2
        wheel_front = half_length - self.WHEEL_POSITION_FROM_FRONT
        wheel_back = wheel_front - self.WHEEL_DIAMETER

        # Create polygon that includes wheel volumes
        vertices = [
            # Front of robot
            (-half_length, -half_width),
            (-half_length, half_width),
            # Front left wheel starts
            (wheel_front, half_width),
            (wheel_front, half_width + wheel_protrusion),
            (wheel_back, half_width + wheel_protrusion),
            (wheel_back, half_width),
            # Back left to back right
            (half_length, half_width),
            (half_length, -half_width),
            # Back right wheel starts
            (wheel_back, -half_width),
            (wheel_back, -half_width - wheel_protrusion),
            (wheel_front, -half_width - wheel_protrusion),
            (wheel_front, -half_width),
        ]
        self.shape = pymunk.Poly(self.body, vertices)
        self.shape.friction = 0.7
        self.shape.elasticity = 0.0  # No bounce - robot shouldn't bounce off walls

        # Add to space
        space.add(self.body, self.shape)
        self.space = space

        # Initialize distance sensor
        # Sensor is mounted at front center: LENGTH/2 - DISTANCE_SENSOR_OFFSET_FROM_FRONT from center
        sensor_local_x = self.LENGTH / 2 - self.DISTANCE_SENSOR_OFFSET_FROM_FRONT
        sensor_local_y = 0.0  # Centered on robot width
        self.distance_sensor = SimulatedVL53L5CX(
            sensor_height=self.DISTANCE_SENSOR_HEIGHT,
            sensor_offset_x=sensor_local_x,
            sensor_offset_y=sensor_local_y,
            glitch_rate=0.01
        )

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
            # Distance sensor control
            self.mqtt_client.subscribe("sensors/distance/control/#")
            self.mqtt_client.message_callback_add(
                "sensors/distance/control/start_ranging", self._on_start_ranging
            )
            self.mqtt_client.message_callback_add(
                "sensors/distance/control/stop_ranging", self._on_stop_ranging
            )
            self.mqtt_client.subscribe("all/stop")
            self.mqtt_client.message_callback_add(
                "all/stop", self._on_stop_ranging
            )
            # Publish ready status
            self.mqtt_client.publish("sensors/distance/status", "ready")

        # Encoder update timing
        self.last_encoder_publish = time.time()
        self.encoder_publish_interval = 0.1  # Publish at 10 Hz like real robot

        # Distance sensor update timing
        self.last_distance_publish = time.time()
        self.distance_publish_interval = 0.1  # 10 Hz matching sensor frequency

    def _on_encoder_reset(self, client, userdata, message):
        """Handle encoder reset MQTT messages.

        Args:
            client: MQTT client
            userdata: User data
            message: MQTT message
        """
        self.left_wheel.reset_encoder()
        self.right_wheel.reset_encoder()

    def _on_start_ranging(self, client, userdata, message):
        """Handle start ranging MQTT messages.

        Args:
            client: MQTT client
            userdata: User data
            message: MQTT message
        """
        self.distance_sensor.start_ranging()

    def _on_stop_ranging(self, client, userdata, message):
        """Handle stop ranging MQTT messages.

        Args:
            client: MQTT client
            userdata: User data
            message: MQTT message
        """
        self.distance_sensor.stop_ranging()

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

    def apply_motor_velocities(self):
        """Apply commanded motor velocities to the robot body.

        Call this BEFORE the physics step so that physics can constrain the motion.
        """
        # Check for motor command timeout
        if self.last_motor_command_time > 0:
            time_since_last_command = time.time() - self.last_motor_command_time
            if time_since_last_command > self.MOTOR_TIMEOUT:
                # Stop motors after timeout
                self.left_wheel.set_speed(0.0)
                self.right_wheel.set_speed(0.0)

        # Get commanded wheel velocities in mm/s
        left_velocity = self.left_wheel.get_velocity()
        right_velocity = self.right_wheel.get_velocity()

        # Calculate differential drive kinematics from commanded velocities
        # Linear velocity (forward) is average of both wheels
        linear_velocity = (left_velocity + right_velocity) / 2.0

        # Angular velocity from difference between wheels
        # omega = (v_right - v_left) / wheel_separation
        angular_velocity_target = (right_velocity - left_velocity) / self.WHEEL_SEPARATION

        # Apply damped velocity control to achieve target velocities
        # This allows pymunk physics to handle collisions and constraints properly
        angle = self.body.angle
        target_vx = linear_velocity * math.cos(angle)
        target_vy = linear_velocity * math.sin(angle)

        # Use exponential damping toward target velocity
        # This provides smooth motion while allowing physics constraints to work
        damping = 0.3  # Higher = faster response (0-1)
        current_vx, current_vy = self.body.velocity
        new_vx = current_vx + (target_vx - current_vx) * damping
        new_vy = current_vy + (target_vy - current_vy) * damping
        new_angular = self.body.angular_velocity + (angular_velocity_target - self.body.angular_velocity) * damping

        self.body.velocity = (new_vx, new_vy)
        self.body.angular_velocity = new_angular

    def update_encoders(self, dt: float):
        """Update encoders based on actual robot motion after physics.

        Call this AFTER the physics step to measure actual constrained motion.

        Args:
            dt: Time step in seconds
        """
        # Calculate actual wheel velocities from body motion
        # Project body velocity onto robot's forward direction
        body_angle = self.body.angle
        forward_x = math.cos(body_angle)
        forward_y = math.sin(body_angle)

        # Get body velocity in world coordinates (mm/s)
        body_vx, body_vy = self.body.velocity

        # Project onto forward direction to get linear velocity
        forward_velocity = body_vx * forward_x + body_vy * forward_y

        # Get angular velocity (rad/s)
        angular_velocity = self.body.angular_velocity

        # Calculate individual wheel velocities from differential drive kinematics
        # v_left = v_forward - (ω * separation/2)
        # v_right = v_forward + (ω * separation/2)
        half_separation = self.WHEEL_SEPARATION / 2
        actual_left_velocity = forward_velocity - (angular_velocity * half_separation)
        actual_right_velocity = forward_velocity + (angular_velocity * half_separation)

        # Update wheel encoders with actual velocities
        self.left_wheel.update_encoder(dt, actual_left_velocity)
        self.right_wheel.update_encoder(dt, actual_right_velocity)

        # Publish encoder data at regular intervals
        current_time = time.time()
        if current_time - self.last_encoder_publish >= self.encoder_publish_interval:
            self._publish_encoder_data()
            self.last_encoder_publish = current_time

    def update_distance_sensor(self, arena_sim):
        """Update distance sensor based on robot position and environment.

        Args:
            arena_sim: Arena simulation object for coordinate conversion
        """
        # Update sensor readings
        self.distance_sensor.update(
            self.x, self.y, self.angle,
            self.space, arena_sim, self.shape,
            debug=False  # Only debug when explicitly requested
        )

        # Publish distance data at regular intervals if ranging
        if self.distance_sensor.is_ranging:
            current_time = time.time()
            if current_time - self.last_distance_publish >= self.distance_publish_interval:
                if self.distance_sensor.data_ready():
                    self._publish_distance_data()
                    self.last_distance_publish = current_time

    def _publish_distance_data(self):
        """Publish distance sensor data to MQTT."""
        if not self.mqtt_client:
            return

        distance_data = self.distance_sensor.get_data()
        publish_json(
            self.mqtt_client,
            "sensors/distance_mm",
            distance_data
        )

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
