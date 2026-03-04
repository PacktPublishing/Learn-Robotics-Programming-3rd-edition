"""Robot sprite for the simulation."""
import pygame
import pygame.gfxdraw
import pymunk
import random
import math
import time
import ujson as json

from common.mqtt_behavior import publish_json
from simulated_vl53l5cx import SimulatedVL53L5CX


class RobotConfiguration:
    """Centralized configuration for simulation calibration and geometry."""

    # Motor speed calibration
    BASE_SPEED_MM_PER_SEC = 195.0  # Mean speed at motor setting 1.0
    SPEED_VARIATION_STDDEV = 5.0   # Standard deviation for motor variation

    # Encoder settings (matching inventor_hat_service.py)
    COUNTS_PER_REV = 32 * 120  # sensor poles * gear ratio
    WHEEL_DIAMETER = 67  # mm
    WHEEL_RADIUS = WHEEL_DIAMETER / 2  # mm

    # Gear lash simulation (encoder can lead wheel motion slightly)
    LASH_ANGLE_DEG = 16.0
    LASH_ANGLE_RADIANS = math.radians(LASH_ANGLE_DEG)
    LASH_VELOCITY_THRESHOLD = 1.0  # mm/s - minimum velocity to treat as motion

    # Robot dimensions (in mm)
    WIDTH = 125  # Chassis width
    LENGTH = 200
    WHEEL_POSITION_FROM_FRONT = 100
    WHEEL_THICKNESS = 25
    WHEEL_SEPARATION = 136  # Center-to-center distance between wheels (measured on real robot)

    # Physics properties
    MASS = 1.0  # kg
    MOMENT_SCALE = 1.0  # Scale factor for moment of inertia

    # Motor timeout
    MOTOR_TIMEOUT = 1.0  # Stop motors after 1 second of no commands

    # Slip + inertia (body motion only, encoders still reflect wheel rotation)
    SLIP_MEAN = 0.03  # Mean slip fraction per wheel (3% loss)
    SLIP_STDDEV = 0.01  # Variation across wheels
    SLIP_MAX = 0.15  # Clamp to avoid extreme loss
    INERTIA_TIME_CONSTANT = 0.12  # Seconds for wheel velocity to settle

    # Contact patch variation (scaled by tire width)
    CONTACT_VARIATION_PER_MM = 0.08  # Max fraction per mm of tire width
    CONTACT_VARIATION_STDDEV = 0.3  # Fraction of max variation (gaussian)
    CONTACT_VARIATION_TAU = 0.5  # Seconds for contact variation to settle
    CONTACT_TURN_FACTOR = 0.2  # Extra variation per rad/s of turning

    # Distance sensor mounting (VL53L5CX)
    DISTANCE_SENSOR_OFFSET_FROM_FRONT = 5  # mm - sensor is 5mm from front edge
    DISTANCE_SENSOR_HEIGHT = 45  # mm - sensor height above floor

    # Display settings
    ROBOT_COLOR = (50, 100, 200)  # Blue
    WHEEL_COLOR = (40, 40, 40)  # Dark gray

    # Timing and control
    ENCODER_PUBLISH_INTERVAL = 0.1  # Publish at 10 Hz like real robot
    DISTANCE_PUBLISH_INTERVAL = 0.1  # 10 Hz matching sensor frequency
    TARGET_VELOCITY_DAMPING = 0.3  # Higher = faster response (0-1)


class RobotWheel:
    """Simulates a robot wheel with motor and encoder characteristics."""

    CONFIG = RobotConfiguration

    def __init__(self):
        """Initialize wheel with random speed variation and encoder."""
        # Add random variation to simulate real motor/gear/wheel differences
        self.speed_factor = random.gauss(
            1.0,
            self.CONFIG.SPEED_VARIATION_STDDEV / self.CONFIG.BASE_SPEED_MM_PER_SEC
        )
        self.current_speed = 0.0  # Current motor speed setting (-1.0 to 1.0)

        # Encoder state
        self.encoder_count = 0.0  # Accumulated encoder counts
        self.encoder_radians = 0.0  # Accumulated radians
        self.last_update_time = time.time()
        self.lash_remaining_radians = 0.0
        self.last_command_direction = 0

    def set_speed(self, speed: float):
        """Set the wheel motor speed.

        Args:
            speed: Motor speed from -1.0 (full reverse) to 1.0 (full forward)
        """
        new_direction = 0
        if speed > 0:
            new_direction = 1
        elif speed < 0:
            new_direction = -1

        if new_direction != self.last_command_direction:
            if new_direction != 0:
                self.lash_remaining_radians = self.CONFIG.LASH_ANGLE_RADIANS
            self.last_command_direction = new_direction

        self.current_speed = max(-1.0, min(1.0, speed))

    def get_velocity(self) -> float:
        """Get the current wheel velocity in mm/s.

        Returns:
            Velocity in mm/s
        """
        return self.current_speed * self.CONFIG.BASE_SPEED_MM_PER_SEC * self.speed_factor

    def get_drive_velocity(self) -> float:
        """Get wheel velocity applied to the robot body, accounting for lash."""
        commanded_velocity = self.get_velocity()
        if self.lash_remaining_radians > 0 and abs(commanded_velocity) >= self.CONFIG.LASH_VELOCITY_THRESHOLD:
            return 0.0
        return commanded_velocity

    def update_encoder(self, dt: float, actual_velocity: float = None):
        """Update encoder counts based on wheel movement.

        Args:
            dt: Time step in seconds
            actual_velocity: Actual wheel velocity in mm/s (from physics).
                           If None, uses commanded velocity.
        """
        # Use actual velocity from physics if provided, otherwise use commanded
        commanded_velocity = self.get_velocity()
        velocity = actual_velocity if actual_velocity is not None else commanded_velocity

        # Apply velocity threshold to simulate static friction and mechanical play
        # Real encoders won't register movement below a minimum threshold
        if abs(velocity) < self.CONFIG.LASH_VELOCITY_THRESHOLD:
            velocity = 0.0

        # Simulate gear lash: encoder may count slightly before wheel motion starts.
        if actual_velocity is not None:
            if abs(actual_velocity) < self.CONFIG.LASH_VELOCITY_THRESHOLD:
                if self.lash_remaining_radians > 0 and abs(commanded_velocity) >= self.CONFIG.LASH_VELOCITY_THRESHOLD:
                    lash_distance_mm = min(
                        abs(commanded_velocity) * dt,
                        self.lash_remaining_radians * self.CONFIG.WHEEL_RADIUS
                    )
                    lash_radians = lash_distance_mm / self.CONFIG.WHEEL_RADIUS
                    self.lash_remaining_radians -= lash_radians
                    self.encoder_radians += math.copysign(lash_radians, commanded_velocity)
            else:
                self.lash_remaining_radians = 0.0

        # Calculate distance traveled in mm
        distance_mm = velocity * dt

        # Convert to radians of wheel rotation
        radians = distance_mm / self.CONFIG.WHEEL_RADIUS

        # Update accumulated values
        self.encoder_radians += radians

        # Convert radians to encoder counts
        counts_per_radian = self.CONFIG.COUNTS_PER_REV / (2 * math.pi)
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
            "counts": self.encoder_count,
            "radians": self.encoder_radians,
                "distance": self.encoder_radians * self.CONFIG.WHEEL_RADIUS,  # mm
            "mm_per_sec": velocity  # mm/s
        }

class Robot:
    """Represents the robot in the simulation."""

    CONFIG = RobotConfiguration

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

        # Slip factors are fixed per wheel for the duration of the run
        self.left_wheel_slip = max(0.0, min(random.gauss(self.CONFIG.SLIP_MEAN, self.CONFIG.SLIP_STDDEV), self.CONFIG.SLIP_MAX))
        self.right_wheel_slip = max(0.0, min(random.gauss(self.CONFIG.SLIP_MEAN, self.CONFIG.SLIP_STDDEV), self.CONFIG.SLIP_MAX))
        self.filtered_left_velocity = 0.0
        self.filtered_right_velocity = 0.0
        self.last_drive_update = time.time()
        self.contact_variation_left = 0.0
        self.contact_variation_right = 0.0

        # Track last motor command time for timeout
        self.last_motor_command_time = 0.0

        # Create pymunk body
        moment = pymunk.moment_for_box(self.CONFIG.MASS, (self.CONFIG.LENGTH, self.CONFIG.WIDTH)) * self.CONFIG.MOMENT_SCALE
        self.body = pymunk.Body(self.CONFIG.MASS, moment)
        self.body.position = (x, y)
        self.body.angle = angle

        # Create shape for the robot body including wheel protrusions
        # Wheels extend WHEEL_THICKNESS beyond the body on each side
        # (wheel center is at WIDTH/2 + WHEEL_THICKNESS/2, plus WHEEL_THICKNESS/2 for wheel radius)
        half_length = self.CONFIG.LENGTH / 2
        half_width = self.CONFIG.WIDTH / 2
        wheel_protrusion = self.CONFIG.WHEEL_THICKNESS  # Full wheel thickness
        wheel_front = half_length - self.CONFIG.WHEEL_POSITION_FROM_FRONT
        wheel_back = wheel_front - self.CONFIG.WHEEL_DIAMETER

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
        sensor_local_x = self.CONFIG.LENGTH / 2 - self.CONFIG.DISTANCE_SENSOR_OFFSET_FROM_FRONT
        sensor_local_y = 0.0  # Centered on robot width
        self.distance_sensor = SimulatedVL53L5CX(
            sensor_height=self.CONFIG.DISTANCE_SENSOR_HEIGHT,
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
        self.encoder_publish_interval = self.CONFIG.ENCODER_PUBLISH_INTERVAL
        self.encoder_seq = 0

        # Distance sensor update timing
        self.last_distance_publish = time.time()
        self.distance_publish_interval = self.CONFIG.DISTANCE_PUBLISH_INTERVAL

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
        now = time.time()
        dt = max(now - self.last_drive_update, 1e-3)
        self.last_drive_update = now

        # Check for motor command timeout
        if self.last_motor_command_time > 0:
            time_since_last_command = time.time() - self.last_motor_command_time
            if time_since_last_command > self.CONFIG.MOTOR_TIMEOUT:
                # Stop motors after timeout
                self.left_wheel.set_speed(0.0)
                self.right_wheel.set_speed(0.0)

        # Get commanded wheel velocities in mm/s
        left_velocity = self.left_wheel.get_drive_velocity()
        right_velocity = self.right_wheel.get_drive_velocity()

        # Apply slip to body motion (encoders still track wheel rotation)
        left_velocity *= (1.0 - self.left_wheel_slip)
        right_velocity *= (1.0 - self.right_wheel_slip)

        # Apply small contact patch variation (bounded by tire width, low-pass filtered)
        turn_rate_estimate = abs(right_velocity - left_velocity) / self.CONFIG.WHEEL_SEPARATION
        max_contact_variation = self.CONFIG.WHEEL_THICKNESS * self.CONFIG.CONTACT_VARIATION_PER_MM
        max_contact_variation *= (1.0 + (turn_rate_estimate * self.CONFIG.CONTACT_TURN_FACTOR))

        target_left_variation = random.gauss(0.0, self.CONFIG.CONTACT_VARIATION_STDDEV) * max_contact_variation
        target_right_variation = random.gauss(0.0, self.CONFIG.CONTACT_VARIATION_STDDEV) * max_contact_variation
        alpha_variation = dt / (self.CONFIG.CONTACT_VARIATION_TAU + dt)
        self.contact_variation_left += (target_left_variation - self.contact_variation_left) * alpha_variation
        self.contact_variation_right += (target_right_variation - self.contact_variation_right) * alpha_variation

        left_variation = max(-max_contact_variation, min(self.contact_variation_left, max_contact_variation))
        right_variation = max(-max_contact_variation, min(self.contact_variation_right, max_contact_variation))
        left_velocity *= (1.0 + left_variation)
        right_velocity *= (1.0 + right_variation)

        # Apply inertia as a first-order lag on wheel velocities
        alpha = dt / (self.CONFIG.INERTIA_TIME_CONSTANT + dt)
        self.filtered_left_velocity += (left_velocity - self.filtered_left_velocity) * alpha
        self.filtered_right_velocity += (right_velocity - self.filtered_right_velocity) * alpha

        # Calculate differential drive kinematics from commanded velocities
        # Linear velocity (forward) is average of both wheels
        linear_velocity = (self.filtered_left_velocity + self.filtered_right_velocity) / 2.0

        # Angular velocity from difference between wheels
        # omega = (v_right - v_left) / wheel_separation
        angular_velocity_target = (self.filtered_right_velocity - self.filtered_left_velocity) / self.CONFIG.WHEEL_SEPARATION

        # Apply damped velocity control to achieve target velocities
        # This allows pymunk physics to handle collisions and constraints properly
        angle = self.body.angle
        target_vx = linear_velocity * math.cos(angle)
        target_vy = linear_velocity * math.sin(angle)

        # Use exponential damping toward target velocity
        # This provides smooth motion while allowing physics constraints to work
        damping = self.CONFIG.TARGET_VELOCITY_DAMPING
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
        half_separation = self.CONFIG.WHEEL_SEPARATION / 2
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
        self.encoder_seq += 1

        publish_json(
            self.mqtt_client,
            "sensors/encoders/data",
            {
                "seq": self.encoder_seq,
                "timestamp_ms": int(time.time() * 1000),
                "left_counts": left_data["counts"],
                "right_counts": right_data["counts"],
                "left_radians": left_data["radians"],
                "right_radians": right_data["radians"],
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
        half_width = self.CONFIG.WIDTH / 2
        half_length = self.CONFIG.LENGTH / 2

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

        # Draw the robot with anti-aliasing
        pygame.gfxdraw.filled_polygon(screen, screen_corners, self.CONFIG.ROBOT_COLOR)
        pygame.gfxdraw.aapolygon(screen, screen_corners, self.CONFIG.ROBOT_COLOR)

        # Draw wheels
        self._draw_wheels(screen, world_to_screen_fn, x, y, cos_a, sin_a)

        # Draw a line to indicate front direction
        front_x = x + (half_length + 20) * cos_a
        front_y = y + (half_length + 20) * sin_a

        center_screen = world_to_screen_fn(x, y)
        front_screen = world_to_screen_fn(front_x, front_y)

        pygame.draw.aaline(screen, (255, 0, 0), center_screen, front_screen, 1)

        # Debug: Draw collision shape outline in green
        if pygame.key.get_pressed()[pygame.K_d]:
            collision_vertices = []
            for vertex in self.shape.get_vertices():
                world_vertex = self.body.local_to_world(vertex)
                collision_vertices.append(world_to_screen_fn(world_vertex.x, world_vertex.y))
            if len(collision_vertices) > 2:
                pygame.draw.aalines(screen, (0, 255, 0), True, collision_vertices, 1)

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
        wheel_offset_x = self.CONFIG.LENGTH / 2 - self.CONFIG.WHEEL_POSITION_FROM_FRONT
        wheel_offset_y = self.CONFIG.WIDTH / 2 + self.CONFIG.WHEEL_THICKNESS / 2

        half_wheel_diameter = self.CONFIG.WHEEL_DIAMETER / 2
        half_wheel_thickness = self.CONFIG.WHEEL_THICKNESS / 2

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

            # Draw the wheel with anti-aliasing
            pygame.gfxdraw.filled_polygon(screen, screen_wheel_corners, self.CONFIG.WHEEL_COLOR)
            pygame.gfxdraw.aapolygon(screen, screen_wheel_corners, self.CONFIG.WHEEL_COLOR)
