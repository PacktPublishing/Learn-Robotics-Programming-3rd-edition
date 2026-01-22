"""Simulated VL53L5CX distance sensor for robot simulation."""
import math
import random
import pymunk


class SimulatedVL53L5CX:
    """Simulates a VL53L5CX time-of-flight distance sensor in 8x8 mode.

    The sensor is modeled as an 8x8 array of zones, where:
    - Rows 0-3 (bottom): Detect floor (constant distance)
    - Rows 4-7 (top): Detect obstacles in front of robot
    """

    # Sensor specifications (based on VL53L5CX datasheet)
    FIELD_OF_VIEW = 45.0  # degrees (45° or 65° depending on configuration)
    MAX_RANGE = 4000  # mm
    MIN_RANGE = 0  # mm
    RESOLUTION = 8  # 8x8 array
    ZONES_TOTAL = 64  # 8x8 = 64 zones

    # Simulation constants
    GLITCH_VALUE = 3000  # mm - value for invalid readings
    DEFAULT_GLITCH_RATE = 0.01  # 1% of readings are glitches

    def __init__(self, sensor_height: float, sensor_offset_x: float, sensor_offset_y: float,
                 glitch_rate: float = DEFAULT_GLITCH_RATE):
        """Initialize the simulated distance sensor.

        Args:
            sensor_height: Height of sensor above floor in mm
            sensor_offset_x: X offset from robot center in mm (local coordinates)
            sensor_offset_y: Y offset from robot center in mm (local coordinates)
            glitch_rate: Probability (0.0-1.0) of generating glitch readings
        """
        self.sensor_height = sensor_height
        self.sensor_offset_x = sensor_offset_x
        self.sensor_offset_y = sensor_offset_y
        self.glitch_rate = glitch_rate
        self.is_ranging = False
        self.data_ready_flag = False
        self.distance_mm = [0] * self.ZONES_TOTAL

        # Calculate angular spacing between zones
        # 8 zones span the full FOV
        self.zone_angular_width = self.FIELD_OF_VIEW / self.RESOLUTION

        # Calculate floor distances for each row using trigonometry
        # Bottom 4 rows can see the floor at different angles
        self.floor_distances = self._calculate_floor_distances()

    def start_ranging(self):
        """Start ranging mode."""
        self.is_ranging = True

    def stop_ranging(self):
        """Stop ranging mode."""
        self.is_ranging = False
        self.data_ready_flag = False

    def data_ready(self) -> bool:
        """Check if new data is ready.

        Returns:
            True if data is ready to be read
        """
        return self.data_ready_flag

    def _calculate_floor_distances(self) -> list[float]:
        """Calculate floor distances for each row based on sensor geometry.

        Uses trigonometry to calculate what distance the sensor should measure
        to the floor based on sensor height and the vertical angle each row observes.

        Returns:
            List of 8 floor distances (one per row) in mm
        """
        floor_distances = []

        # Each row looks at a different vertical angle within the FOV
        # Row 0 (bottom) looks at -FOV/2 + half_row_angle
        # Row 7 (top) looks at +FOV/2 - half_row_angle
        half_fov = self.FIELD_OF_VIEW / 2.0

        for row in range(self.RESOLUTION):
            # Calculate vertical angle for this row (negative = looking down)
            # Row 0 is at bottom: -half_fov + (row + 0.5) * zone_angular_width
            # Row 7 is at top: +half_fov - (7 - row + 0.5) * zone_angular_width
            row_angle = -half_fov + (row + 0.5) * self.zone_angular_width

            # Only bottom rows can see the floor (negative angles)
            if row_angle < 0:
                # Distance = height / sin(angle_magnitude)
                # Using Pythagoras: if sensor is h above floor looking down at angle θ,
                # the measured distance along the ray is h / sin(|θ|)
                angle_rad = math.radians(abs(row_angle))
                floor_dist = self.sensor_height / math.sin(angle_rad)
                floor_distances.append(min(floor_dist, self.MAX_RANGE))
            else:
                # Upper rows can't see floor
                floor_distances.append(self.MAX_RANGE)

        return floor_distances

    def update(self, robot_x: float, robot_y: float, robot_angle: float,
               space: pymunk.Space, arena_sim, robot_shape: pymunk.Shape,
               debug: bool = False):
        """Update sensor readings based on robot position and environment.

        Args:
            robot_x: Robot X position in mm
            robot_y: Robot Y position in mm
            robot_angle: Robot orientation in radians
            space: Pymunk space containing obstacles
            arena_sim: Arena simulation object for coordinate conversion
            robot_shape: Robot's pymunk shape to exclude from raycasts
            debug: If True, print debug information for middle column
        """
        if not self.is_ranging:
            return

        # Calculate sensor position from robot center using local offset
        # Rotate the local offset by robot angle to get world offset
        cos_angle = math.cos(robot_angle)
        sin_angle = math.sin(robot_angle)
        world_offset_x = self.sensor_offset_x * cos_angle - self.sensor_offset_y * sin_angle
        world_offset_y = self.sensor_offset_x * sin_angle + self.sensor_offset_y * cos_angle

        sensor_x = robot_x + world_offset_x
        sensor_y = robot_y + world_offset_y

        # Raycast once per column (8 times for 8 columns)
        # In 2D, all zones in same column have same obstacle distance
        column_distances = []
        for col in range(self.RESOLUTION):
            obstacle_distance = self._raycast_zone(
                sensor_x, sensor_y, robot_angle,
                col, space, robot_shape, debug=(debug and col == 4)  # Debug middle column only if debug=True
            )
            column_distances.append(obstacle_distance)

        # Update each zone in the 8x8 array
        for row in range(self.RESOLUTION):
            for col in range(self.RESOLUTION):
                zone_index = row * self.RESOLUTION + col

                # Get obstacle distance for this column
                obstacle_distance = column_distances[col]

                # Use floor distance for this row if closer than obstacle
                floor_distance = self.floor_distances[row]
                distance = min(obstacle_distance, floor_distance)

                # Apply glitches randomly
                if random.random() < self.glitch_rate:
                    distance = self.GLITCH_VALUE

                self.distance_mm[zone_index] = int(distance)

        self.data_ready_flag = True

    def _raycast_zone(self, sensor_x: float, sensor_y: float,
                      robot_angle: float, col: int,
                      space: pymunk.Space, robot_shape: pymunk.Shape, debug: bool = False) -> float:
        """Perform raycast for a specific column to detect obstacles.

        Args:
            sensor_x: Sensor X position in mm
            sensor_y: Sensor Y position in mm
            robot_angle: Robot orientation in radians
            col: Zone column (0-7)
            space: Pymunk space containing obstacles
            robot_shape: Robot's shape to exclude from raycast
            debug: If True, print debug information

        Returns:
            Distance to obstacle in mm, or MAX_RANGE if nothing detected
        """
        # Calculate angle for this column
        # Column 0 is leftmost (-FOV/2), column 7 is rightmost (+FOV/2)
        col_offset = (col - 3.5) * self.zone_angular_width
        ray_angle = robot_angle + math.radians(col_offset)

        # Cast ray from sensor position
        ray_start = pymunk.Vec2d(sensor_x, sensor_y)
        ray_direction = pymunk.Vec2d(
            math.cos(ray_angle),
            math.sin(ray_angle)
        )
        ray_end = ray_start + ray_direction * self.MAX_RANGE

        if debug:
            print(f"    Raycast col {col}: start=({sensor_x:.1f}, {sensor_y:.1f}), angle={math.degrees(ray_angle):.1f}°, end=({ray_end.x:.1f}, {ray_end.y:.1f})")

        # Perform raycast to get ALL hits
        queries = space.segment_query(
            ray_start, ray_end,
            0,  # radius
            pymunk.ShapeFilter()  # detect all shapes
        )

        if debug:
            print(f"    Found {len(queries)} hit(s)")

        # Filter out hits to the robot's own shape and find closest valid hit
        min_distance = self.MAX_RANGE
        closest_hit = None

        for query in queries:
            if query.shape == robot_shape:
                if debug:
                    print(f"    Ignoring hit on robot body at ({query.point.x:.1f}, {query.point.y:.1f})")
                continue

            # Calculate distance to this hit point
            hit_point = query.point
            distance = math.sqrt(
                (hit_point.x - sensor_x) ** 2 +
                (hit_point.y - sensor_y) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                closest_hit = query

        if closest_hit is not None:
            if debug:
                print(f"    Closest valid hit at ({closest_hit.point.x:.1f}, {closest_hit.point.y:.1f}), distance={min_distance:.1f}mm")
            return min(min_distance, self.MAX_RANGE)

        if debug:
            print("    No valid hits detected")
        return self.MAX_RANGE

    def get_data(self):
        """Get current distance data.

        Returns:
            List of 64 distance values in mm (8x8 array, row-major order)
        """
        self.data_ready_flag = False
        return self.distance_mm.copy()
