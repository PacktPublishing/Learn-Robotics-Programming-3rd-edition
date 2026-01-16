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
