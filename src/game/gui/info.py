import pygame
from pygame_gui.elements import UILabel, UIPanel


class InfoPanel:
    """Info panel using pygame_gui built-in elements."""

    def __init__(self, manager, env_size, panel_width):
        """Initialize the info panel with pygame_gui elements."""
        self.manager = manager
        self.panel_x = env_size
        self.panel_width = panel_width
        self.env_size = env_size

        # Create main panel
        self.panel = UIPanel(
            relative_rect=pygame.Rect(self.panel_x, 0, panel_width, env_size),
            manager=manager,
        )

        # Layout constants
        PADDING_X = 30
        content_width = panel_width - (PADDING_X * 2)

        # Title
        self.title = UILabel(
            relative_rect=pygame.Rect(0, 20, panel_width, 40),
            text="MISSION INFORMATION",
            manager=manager,
            container=self.panel,
            object_id="#title",
        )

        # Victims section
        self.victims_header = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 10, content_width, 30),
            text="VICTIMS",
            manager=manager,
            container=self.panel,
            object_id="#section_header",
            anchors={"top": "top", "top_target": self.title},
        )

        self.rescued_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 5, content_width, 30),
            text="Rescued: 0",
            manager=manager,
            container=self.panel,
            object_id="label",
            anchors={"top": "top", "top_target": self.victims_header},
        )

        self.remaining_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 5, content_width, 30),
            text="Remaining: 0",
            manager=manager,
            container=self.panel,
            anchors={"top": "top", "top_target": self.rescued_label},
        )

        self.score_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 5, content_width, 30),
            text="Score: 0",
            manager=manager,
            container=self.panel,
            anchors={"top": "top", "top_target": self.remaining_label},
        )

        # Time & Inventory section
        self.time_header = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 20, content_width, 30),
            text="TIME & INVENTORY",
            manager=manager,
            container=self.panel,
            object_id="#section_header",
            anchors={"top": "top", "top_target": self.score_label},
        )

        self.steps_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 10, content_width, 30),
            text="Steps: 0 / 0",
            manager=manager,
            container=self.panel,
            anchors={"top": "top", "top_target": self.time_header},
        )

        self.inventory_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, 10, content_width, 30),
            text="Inventory: None",
            manager=manager,
            container=self.panel,
            anchors={"top": "top", "top_target": self.steps_label},
        )

        # Status message (anchored to bottom)
        self.status_label = UILabel(
            relative_rect=pygame.Rect(PADDING_X, -50, content_width, 40),
            text="",
            manager=manager,
            container=self.panel,
            object_id="#success_text",
            anchors={"bottom": "bottom"},
        )

    def _update_victims_section(self, mission_status):
        """Update the victims section labels."""
        saved = mission_status.get("saved_victims", 0)
        remaining = mission_status.get("remaining_victims", 0)

        self.rescued_label.set_text(f"Rescued: {saved}")
        self.remaining_label.set_text(f"Remaining: {remaining}")
        self.score_label.set_text(f"Score: {saved * 10}")

        # Update remaining color based on count
        if remaining > 0:
            self.remaining_label.change_object_id("#danger_text")
        else:
            self.remaining_label.change_object_id("#success_text")

    def _update_time_and_inventory(self, env):
        """Update time and inventory labels."""
        steps = getattr(env, "step_count", 0)
        max_steps = getattr(env, "max_steps", 0)
        carrying = getattr(env, "carrying", None)

        self.steps_label.set_text(f"Steps: {steps} / {max_steps}")

        if carrying:
            inventory_text = f"Inventory: {carrying.color.capitalize()} Key"
            # Set color based on key color
            key_color_map = {
                "red": "#red_key",
                "green": "#green_key",
                "blue": "#blue_key",
                "yellow": "#yellow_key",
                "purple": "#purple_key",
                "grey": "#grey_key",
            }
            color_id = key_color_map.get(carrying.color.lower(), "#info_text")
            self.inventory_label.change_object_id(color_id)
            self.inventory_label.set_text(inventory_text)
        else:
            self.inventory_label.change_object_id("label")
            self.inventory_label.set_text("Inventory: None")

    def _update_status(self, mission_status):
        """Update the status message label."""
        status = mission_status.get("status", "incomplete")
        if status == "success":
            self.status_label.change_object_id("#success_text")
            self.status_label.set_text("MISSION COMPLETE!")
        elif status == "failure":
            self.status_label.change_object_id("#danger_text")
            self.status_label.set_text("MISSION FAILED")
        else:
            self.status_label.set_text("")

    def render(self, env):
        """Update the panel with current game state."""
        mission_status = env.get_mission_status()
        self._update_victims_section(mission_status)
        self._update_time_and_inventory(env)
        self._update_status(mission_status)
