import pygame


class Fonts:
    """Centralized font management."""

    _initialized = False
    title_font = None
    section_font = None
    text_font = None

    @classmethod
    def init(cls):
        """Initialize fonts once."""
        if not cls._initialized:
            pygame.font.init()
            cls.title_font = pygame.font.Font(None, 36)
            cls.section_font = pygame.font.Font(None, 28)
            cls.text_font = pygame.font.Font(None, 24)
            cls._initialized = True


class DrawUtils:
    """Common drawing utilities for GUI panels."""

    @staticmethod
    def draw_panel_background(surface, x, y, width, height):
        """Draw a panel background with border."""
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, ColorPalette.BG_COLOR, panel_rect)
        pygame.draw.rect(surface, ColorPalette.BORDER_COLOR, panel_rect, 3)

    @staticmethod
    def draw_title(surface, x, y, width, title_text):
        """Draw centered title with separator line. Returns new y position."""
        Fonts.init()
        title = Fonts.title_font.render(title_text, True, ColorPalette.TITLE_COLOR)
        title_x = x + (width - title.get_width()) // 2
        surface.blit(title, (title_x, y))
        y += 50
        pygame.draw.line(surface, ColorPalette.TITLE_COLOR, (x, y), (x + width, y), 3)
        return y + 20

    @staticmethod
    def draw_section_header(surface, x, y, width, header_text):
        """Draw section header with underline. Returns new y position."""
        Fonts.init()
        header = Fonts.section_font.render(header_text, True, ColorPalette.TITLE_COLOR)
        surface.blit(header, (x, y))
        y += 30
        pygame.draw.line(surface, ColorPalette.SECTION_LINE_COLOR, (x, y), (x + width, y), 2)
        return y + 15

    @staticmethod
    def draw_label_value_pair(surface, x, y, width, label, value, value_color):
        """Draw a label-value pair with value right-aligned."""
        Fonts.init()
        label_text = Fonts.text_font.render(label, True, ColorPalette.TEXT_COLOR)
        value_text = Fonts.text_font.render(value, True, value_color)
        surface.blit(label_text, (x, y))
        surface.blit(value_text, (x + width - value_text.get_width(), y))


class GUIElements:
    """Collection of reusable GUI drawing functions and visual elements."""

    @staticmethod
    def draw_progress_bar(surface, x, y, width, height, progress, bg_color, fill_color):
        """
        Draw a fancy progress bar with shine effect.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            width, height: Dimensions of the progress bar
            progress: Progress value (0.0 to 1.0)
            bg_color: Background color
            fill_color: Fill color for the progress
        """
        # Background
        pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=5)
        # Border
        pygame.draw.rect(surface, (80, 80, 90), (x, y, width, height), 2, border_radius=5)

        # Fill
        if progress > 0:
            fill_width = int(width * min(progress, 1.0))
            pygame.draw.rect(surface, fill_color, (x, y, fill_width, height), border_radius=5)

            # Shine effect on top
            shine_height = height // 3
            shine_color = tuple(min(255, c + 40) for c in fill_color)
            pygame.draw.rect(
                surface, shine_color, (x, y, fill_width, shine_height), border_radius=5
            )

    @staticmethod
    def draw_icon_victim(surface, x, y, size, color):
        """
        Draw a victim icon (cross shape).

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            size: Size of the icon
            color: Color of the icon
        """
        center_x = x + size // 2
        center_y = y + size // 2
        arm_width = size // 5

        # Vertical bar
        pygame.draw.rect(
            surface,
            color,
            (center_x - arm_width // 2, y, arm_width, size),
            border_radius=2,
        )
        # Horizontal bar
        pygame.draw.rect(
            surface,
            color,
            (x, center_y - arm_width // 2, size, arm_width),
            border_radius=2,
        )

    @staticmethod
    def draw_icon_star(surface, x, y, size, color):
        """
        Draw a star icon for points/score.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            size: Size of the icon
            color: Color of the icon
        """
        center_x = x + size // 2
        center_y = y + size // 2
        points = []
        for i in range(10):
            angle = i * 36 - 90
            radius = size // 2 if i % 2 == 0 else size // 4
            px = center_x + int(radius * pygame.math.Vector2(1, 0).rotate(angle).x)
            py = center_y + int(radius * pygame.math.Vector2(1, 0).rotate(angle).y)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)

    @staticmethod
    def draw_icon_clock(surface, x, y, size, color):
        """
        Draw a clock icon for time tracking.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            size: Size of the icon
            color: Color of the icon
        """
        center_x = x + size // 2
        center_y = y + size // 2
        radius = size // 2

        # Circle outline
        pygame.draw.circle(surface, color, (center_x, center_y), radius, 2)

        # Clock hands
        pygame.draw.line(
            surface, color, (center_x, center_y), (center_x, center_y - radius // 2), 2
        )
        pygame.draw.line(
            surface, color, (center_x, center_y), (center_x + radius // 3, center_y), 2
        )

    @staticmethod
    def draw_icon_key(surface, x, y, size, color):
        """
        Draw a key icon for inventory display.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            size: Size of the icon
            color: Color of the icon
        """
        # Key head (circle)
        head_radius = size // 4
        head_x = x + head_radius + 2
        head_y = y + size // 2
        pygame.draw.circle(surface, color, (head_x, head_y), head_radius, 2)

        # Key shaft
        shaft_width = size // 2
        shaft_height = size // 6
        shaft_x = head_x + head_radius
        shaft_y = head_y - shaft_height // 2
        pygame.draw.rect(surface, color, (shaft_x, shaft_y, shaft_width, shaft_height))

        # Key teeth
        teeth_x = shaft_x + shaft_width - 2
        for i in range(2):
            tooth_y = shaft_y + shaft_height + i * 4
            pygame.draw.rect(surface, color, (teeth_x, tooth_y, 3, 3))

    @staticmethod
    def draw_section_header(surface, x, y, text, icon_func, icon_color, panel_width, section_font, title_color):
        """
        Draw a fancy section header with icon and underline.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            text: Header text
            icon_func: Function to draw the icon
            icon_color: Color of the icon
            panel_width: Width of the panel for underline
            section_font: Font for the section text
            title_color: Color of the title text

        Returns:
            int: Y position after the header (for next element)
        """
        # Draw icon
        icon_size = 24
        icon_func(surface, x, y, icon_size, icon_color)

        # Draw text
        text_surface = section_font.render(text, True, title_color)
        surface.blit(text_surface, (x + icon_size + 10, y))

        # Draw underline
        line_y = y + 28
        pygame.draw.line(
            surface, (80, 80, 90), (x, line_y), (x + panel_width - 40, line_y), 2
        )

        return line_y + 10

    @staticmethod
    def draw_status_box(surface, x, y, width, height, status_text, status_text2, status_color, section_font):
        """
        Draw a fancy status box with border and text.

        Args:
            surface: Pygame surface to draw on
            x, y: Top-left position
            width, height: Dimensions of the box
            status_text: First line of status text
            status_text2: Second line of status text
            status_color: Color for border and text
            section_font: Font for the status text
        """
        # Status box background
        status_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (20, 20, 30), status_rect, border_radius=10)
        pygame.draw.rect(surface, status_color, status_rect, 3, border_radius=10)

        # Status text
        status_line1 = section_font.render(status_text, True, status_color)
        status_line2 = section_font.render(status_text2, True, status_color)

        text1_x = x + (width - status_line1.get_width()) // 2
        text2_x = x + (width - status_line2.get_width()) // 2

        surface.blit(status_line1, (text1_x, y + 10))
        surface.blit(status_line2, (text2_x, y + 35))


class ColorPalette:
    """Color palette for the GUI."""

    BG_COLOR = (30, 30, 40)
    TITLE_COLOR = (255, 255, 255)  # Pure white
    TEXT_COLOR = (220, 220, 220)
    SUCCESS_COLOR = (50, 205, 50)  # Lime green
    DANGER_COLOR = (220, 20, 60)  # Crimson
    WARNING_COLOR = (255, 165, 0)  # Orange
    INFO_COLOR = (100, 149, 237)  # Cornflower blue
    BORDER_COLOR = (60, 60, 70)
    SECTION_LINE_COLOR = (80, 80, 90)

    # Key colors for inventory display
    KEY_COLORS = {
        "Red": (255, 0, 0),
        "Green": (0, 255, 0),
        "Blue": (0, 100, 255),
        "Yellow": (255, 255, 0),
        "Purple": (160, 32, 240),
        "Grey": (128, 128, 128),
    }
