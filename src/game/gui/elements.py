import pygame
from pygame_gui.elements import UIButton, UILabel, UIPanel


def generate_elements(manager, env_size, panel_width):
    elements = {}

    panel_height = env_size
    panel = UIPanel(
        relative_rect=(env_size, 0, panel_width, panel_height),
        starting_height=1,
        manager=manager,
    )

    # Movement buttons container (grid-like manual positions)
    button_width, button_height = 100, 50
    button_padding = 20
    elements = {}

    # Move Up / Down (already correct)
    elements["move_up_button"] = UIButton(
        relative_rect=pygame.Rect(
            (button_padding + 75, button_padding), (button_width, button_height)
        ),
        text="Move Up",
        manager=manager,
        container=panel,
    )

    up_rect = elements["move_up_button"].relative_rect
    elements["move_down_button"] = UIButton(
        relative_rect=pygame.Rect(
            (up_rect.left, up_rect.bottom + button_padding),
            (button_width, button_height),
        ),
        text="Move Down",
        manager=manager,
        container=panel,
    )

    # Move Left / Right placed to the right of Up/Down buttons
    elements["move_left_button"] = UIButton(
        relative_rect=pygame.Rect(
            (up_rect.right + button_padding, up_rect.top),
            (button_width, button_height),
        ),
        text="Move Left",
        manager=manager,
        container=panel,
    )

    elements["move_right_button"] = UIButton(
        relative_rect=pygame.Rect(
            (up_rect.right + button_padding, up_rect.bottom + button_padding),
            (button_width, button_height),
        ),
        text="Move Right",
        manager=manager,
        container=panel,
    )

    # Labels below buttons
    label_y = (
        2 * (button_height + button_padding) + button_padding
    )  # leave space after buttons

    elements["reward_label"] = UILabel(
        relative_rect=pygame.Rect((0, label_y), (panel_width - 20, 30)),
        text="Reward: 0",
        manager=manager,
        container=panel,
    )

    elements["step_label"] = UILabel(
        relative_rect=pygame.Rect((0, label_y + 35), (panel_width - 20, 30)),
        text="Steps: 0",
        manager=manager,
        container=panel,
    )

    return elements
