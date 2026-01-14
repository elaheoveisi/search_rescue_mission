import pygame

from .elements import ColorPalette, DrawUtils, Fonts


class ChatPanel:
    """Chat panel for displaying messages and communication."""

    def __init__(self, x_position, y_position, panel_width, panel_height):
        """Initialize the chat panel."""
        self.panel_x = x_position
        self.panel_y = y_position
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.messages = []
        Fonts.init()

    def render(self, surface):
        """Render the chat panel."""
        # Background and border
        DrawUtils.draw_panel_background(
            surface, self.panel_x, self.panel_y, self.panel_width, self.panel_height
        )

        # Content area
        x = self.panel_x + 20
        y = self.panel_y + 20
        width = self.panel_width - 40

        # Title
        y = DrawUtils.draw_title(surface, x, y, width, "CHAT")

        # Placeholder text
        placeholder = Fonts.text_font.render("Chat panel ready...", True, ColorPalette.TEXT_COLOR)
        surface.blit(placeholder, (x, y))

    def add_message(self, message):
        """Add a message to the chat."""
        self.messages.append(message)

    def clear_messages(self):
        """Clear all messages from the chat."""
        self.messages = []
