import pygame
from pygame_gui.elements import UIPanel, UILabel


class ChatPanel:
    """Chat panel using pygame_gui built-in elements."""

    def __init__(self, manager, x_position, y_position, panel_width, panel_height):
        """Initialize the chat panel with pygame_gui elements."""
        self.manager = manager
        self.panel_x = x_position
        self.panel_y = y_position
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.messages = []

        # Create main panel
        self.panel = UIPanel(
            relative_rect=pygame.Rect(x_position, y_position, panel_width, panel_height),
            manager=manager,
        )

        # Title
        self.title = UILabel(
            relative_rect=pygame.Rect(0, 20, panel_width, 40),
            text="CHAT",
            manager=manager,
            container=self.panel,
            object_id="#title",
        )

        # Placeholder text
        self.placeholder = UILabel(
            relative_rect=pygame.Rect(20, 80, panel_width - 40, 30),
            text="Chat panel ready...",
            manager=manager,
            container=self.panel,
        )

    def render(self):
        """Update the chat panel (placeholder for now)."""
        pass

    def add_message(self, message):
        """Add a message to the chat."""
        self.messages.append(message)

    def clear_messages(self):
        """Clear all messages from the chat."""
        self.messages = []
