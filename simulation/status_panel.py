"""Status panel for displaying simulation state."""
import math
import pygame


class StatusPanel:
    """Displays robot and simulation status information."""

    # Panel settings
    WIDTH = 250  # Width of status panel in pixels
    BACKGROUND_COLOR = (0, 0, 0)  # Black background
    TEXT_COLOR = (0, 191, 255)  # Electric blue (deep sky blue)
    TITLE_COLOR = (135, 206, 250)  # Lighter blue for titles (light sky blue)
    BORDER_COLOR = (0, 0, 0)

    def __init__(self, x_offset: int, height: int):
        """Initialize the status panel.

        Args:
            x_offset: X position where panel starts (pixels)
            height: Height of the panel (pixels)
        """
        self.x_offset = x_offset
        self.height = height

        pygame.font.init()
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen: pygame.Surface, robot):
        """Draw status information panel.

        Args:
            screen: Pygame surface to draw on
            robot: Robot instance to display status for
        """
        # Draw status panel background
        panel_rect = pygame.Rect(self.x_offset, 0, self.WIDTH, self.height)
        pygame.draw.rect(screen, self.BACKGROUND_COLOR, panel_rect)
        pygame.draw.line(
            screen, self.BORDER_COLOR,
            (self.x_offset, 0),
            (self.x_offset, self.height),
            2
        )

        # Status text starting position
        x_pos = self.x_offset + 10
        y_pos = 20
        line_height = 30

        # Get robot data
        left_data = robot.left_wheel.get_encoder_data()
        right_data = robot.right_wheel.get_encoder_data()
        sensor_status = "ACTIVE" if robot.distance_sensor.is_ranging else "INACTIVE"

        # Robot position and orientation
        pos_x, pos_y = robot.body.position
        angle_rad = robot.body.angle
        angle_deg = angle_rad * 180 / math.pi

        # Robot Position Section
        title_surface = self.font.render("ROBOT POSITION", True, self.TITLE_COLOR)
        screen.blit(title_surface, (x_pos, y_pos))
        y_pos += line_height

        pos_lines = [
            f"X: {pos_x:.1f} mm",
            f"Y: {pos_y:.1f} mm",
            f"Angle: {angle_deg:.1f}°",
        ]
        for line in pos_lines:
            text_surface = self.font.render(line, True, self.TEXT_COLOR)
            screen.blit(text_surface, (x_pos, y_pos))
            y_pos += line_height

        y_pos += line_height // 2  # Small gap

        # Encoder Status Section - Table Format
        title_surface = self.font.render("ENCODER STATUS", True, self.TITLE_COLOR)
        screen.blit(title_surface, (x_pos, y_pos))
        y_pos += line_height

        # Table header with background shading
        header_y = y_pos
        col1_x = x_pos + 80  # Left column
        col2_x = x_pos + 150  # Right column

        # Draw header background
        header_rect = pygame.Rect(x_pos, header_y, self.WIDTH - 20, line_height - 5)
        pygame.draw.rect(screen, (0, 0, 0), header_rect)

        # Draw header text
        header_text = self.font.render("Left", True, self.TITLE_COLOR)
        screen.blit(header_text, (col1_x, y_pos))
        header_text = self.font.render("Right", True, self.TITLE_COLOR)
        screen.blit(header_text, (col2_x, y_pos))
        y_pos += line_height

        # Table rows
        rows = [
            ("Speed", f"{robot.left_wheel.current_speed:.1f}", f"{robot.right_wheel.current_speed:.1f}"),
            ("Count", f"{robot.left_wheel.encoder_count:.0f}", f"{robot.right_wheel.encoder_count:.0f}"),
            ("Dist (mm)", f"{left_data['distance']:.1f}", f"{right_data['distance']:.1f}"),
        ]

        for i, (label, left_val, right_val) in enumerate(rows):
            # Green background for count row
            if label == "Count":
                row_rect = pygame.Rect(x_pos, y_pos - 2, self.WIDTH - 20, line_height - 5)
                pygame.draw.rect(screen, (20, 40, 20), row_rect)  # Faint green

            # Row label with background shading
            label_rect = pygame.Rect(x_pos, y_pos, 75, line_height - 5)
            pygame.draw.rect(screen, (0, 0, 0), label_rect)

            label_text = self.font.render(label, True, self.TITLE_COLOR)
            screen.blit(label_text, (x_pos + 5, y_pos))

            # Values
            left_text = self.font.render(left_val, True, self.TEXT_COLOR)
            screen.blit(left_text, (col1_x, y_pos))

            right_text = self.font.render(right_val, True, self.TEXT_COLOR)
            screen.blit(right_text, (col2_x, y_pos))

            y_pos += line_height

        y_pos += line_height // 2  # Small gap

        # Distance Sensor Section
        title_surface = self.font.render("DISTANCE SENSOR", True, self.TITLE_COLOR)
        screen.blit(title_surface, (x_pos, y_pos))
        y_pos += line_height

        status_text = self.font.render(f"Status: {sensor_status}", True, self.TEXT_COLOR)
        screen.blit(status_text, (x_pos, y_pos))

    def log_status_snapshot(self, robot, arena_sim):
        """Log robot status snapshot to terminal for debugging.

        Args:
            robot: Robot instance to log status for
            arena_sim: Arena simulation instance for debug update
        """
        print("\n" + "=" * 60)
        print("STATUS SNAPSHOT")
        print("=" * 60)

        # Robot position
        pos_x, pos_y = robot.body.position
        angle_rad = robot.body.angle
        angle_deg = angle_rad * 180 / math.pi

        print("\nROBOT POSITION:")
        print(f"  X: {pos_x:.1f} mm")
        print(f"  Y: {pos_y:.1f} mm")
        print(f"  Angle: {angle_deg:.1f}° ({angle_rad:.3f} rad)")

        # Encoder status
        left_data = robot.left_wheel.get_encoder_data()
        right_data = robot.right_wheel.get_encoder_data()

        print("\nENCODER STATUS:")
        print(f"  {'':12s} {'Left':>10s} {'Right':>10s}")
        print(f"  {'Speed':12s} {robot.left_wheel.current_speed:>10.1f} {robot.right_wheel.current_speed:>10.1f}")
        print(f"  {'Count':12s} {robot.left_wheel.encoder_count:>10.0f} {robot.right_wheel.encoder_count:>10.0f}")
        print(f"  {'Dist (mm)':12s} {left_data['distance']:>10.1f} {right_data['distance']:>10.1f}")

        # Distance sensor
        sensor_status = "ACTIVE" if robot.distance_sensor.is_ranging else "INACTIVE"
        print("\nDISTANCE SENSOR:")
        print(f"  Status: {sensor_status}")
        print(f"  Sensor position: ({robot.distance_sensor.sensor_offset_x:.1f}, {robot.distance_sensor.sensor_offset_y:.1f}) mm from robot center")

        if robot.distance_sensor.is_ranging:
            print("  Debug raycast (middle column):")
            # Calculate sensor world position
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            world_offset_x = robot.distance_sensor.sensor_offset_x * cos_angle - robot.distance_sensor.sensor_offset_y * sin_angle
            world_offset_y = robot.distance_sensor.sensor_offset_x * sin_angle + robot.distance_sensor.sensor_offset_y * cos_angle
            sensor_x = pos_x + world_offset_x
            sensor_y = pos_y + world_offset_y
            print(f"    Sensor world pos: ({sensor_x:.1f}, {sensor_y:.1f})")

            # Show arena boundaries
            print("    Arena boundaries: x=[0, 1500], y=[0, 1500]")
            print(f"    Distance to walls: left={sensor_x:.1f}mm, right={1500-sensor_x:.1f}mm, bottom={sensor_y:.1f}mm, top={1500-sensor_y:.1f}mm")
            print(f"    Shapes in space: {len(robot.space.shapes)}")

            # Trigger one debug update to see raycast details
            print("    Calling sensor update with debug=True...")
            robot.distance_sensor.update(
                pos_x, pos_y, angle_rad,
                robot.space, arena_sim, robot.shape,
                debug=True
            )

            # Get sensor data and display all 8 rows
            sensor_data = robot.distance_sensor.get_data()

            print("\n  All Rows (8x8 array):")
            print(f"  {'Row':>4s}  Zone:  ", end="")
            for i in range(8):
                print(f"{i:>6d}", end="")
            print()
            print(f"  {'-'*60}")

            for row in range(8):
                row_data = sensor_data[row*8:(row+1)*8]
                print(f"  {row:>4d}        ", end="")
                for dist in row_data:
                    print(f"{dist:>6.0f}", end="")
                print()

        print("=" * 60 + "\n")
