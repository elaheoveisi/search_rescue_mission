from .elements import ColorPalette, DrawUtils, Fonts


class InfoPanel:
    """Clean info panel to display game statistics and mission status."""

    def __init__(self, env_size, panel_width):
        """Initialize the info panel."""
        self.env_size = env_size
        self.panel_width = panel_width
        self.panel_x = env_size
        Fonts.init()

    def render(self, surface, env):
        """Render the info panel."""
        # Background and border
        DrawUtils.draw_panel_background(
            surface, self.panel_x, 0, self.panel_width, self.env_size
        )

        # Content area
        x = self.panel_x + 20
        y = 20
        width = self.panel_width - 40

        # Title
        y = DrawUtils.draw_title(surface, x, y, width, "MISSION CONTROL")

        # Get mission data
        mission_status = env.get_mission_status()
        saved = mission_status.get("saved_victims", 0)
        remaining = mission_status.get("remaining_victims", 0)

        # Victims section
        y = self._draw_section(
            surface,
            x,
            y,
            width,
            "VICTIMS",
            [
                ("Rescued:", str(saved), ColorPalette.SUCCESS_COLOR),
                (
                    "Remaining:",
                    str(remaining),
                    ColorPalette.DANGER_COLOR
                    if remaining > 0
                    else ColorPalette.TEXT_COLOR,
                ),
                ("Score:", str(saved * 10), ColorPalette.TITLE_COLOR),
            ],
        )

        # Time & Inventory section
        steps = getattr(env, "step_count", 0)
        max_steps = getattr(env, "max_steps", 0)
        carrying = getattr(env, "carrying", None)

        inventory_value = "None"
        inventory_color = (100, 100, 110)
        if carrying:
            inventory_value = f"{carrying.color.capitalize()} Key"
            inventory_color = ColorPalette.KEY_COLORS.get(
                carrying.color.capitalize(), (255, 255, 255)
            )

        y = self._draw_section(
            surface,
            x,
            y,
            width,
            "TIME & INVENTORY",
            [
                ("Steps:", f"{steps} / {max_steps}", ColorPalette.INFO_COLOR),
                ("Inventory:", inventory_value, inventory_color),
            ],
        )

        # Status (only if mission ended)
        status = mission_status.get("status", "incomplete")
        if status == "success":
            self._draw_status(
                surface, x, "MISSION COMPLETE!", ColorPalette.SUCCESS_COLOR
            )
        elif status == "failure":
            self._draw_status(surface, x, "MISSION FAILED", ColorPalette.DANGER_COLOR)

    def _draw_section(self, surface, x, y, width, header, items):
        """Draw a section with header and items."""
        # Header with underline
        y = DrawUtils.draw_section_header(surface, x, y, width, header)

        # Items (label, value, color)
        for label, value, color in items:
            DrawUtils.draw_label_value_pair(surface, x, y, width, label, value, color)
            y += 30

        return y + 15

    def _draw_status(self, surface, x, text, color):
        """Draw status message at bottom."""
        status_label = Fonts.section_font.render(text, True, color)
        surface.blit(status_label, (x, self.env_size - 50))
