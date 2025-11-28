import pygame
import pygame_gui


def generate_elements(manager):
    elements = {}

    elements["move_up_button"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 10), (100, 50)),
        text="Move Up",
        manager=manager,
    )

    elements["move_down_button"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((120, 10), (100, 50)),
        text="Move Down",
        manager=manager,
    )

    elements["move_left_button"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((10, 70), (100, 50)),
        text="Move Left",
        manager=manager,
    )

    elements["move_right_button"] = pygame_gui.elements.UIButton(
        relative_rect=pygame.Rect((120, 70), (100, 50)),
        text="Move Right",
        manager=manager,
    )

    elements["reward_label"] = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 130), (300, 30)),
        text="Reward: 0",
        manager=manager,
    )

    elements["step_label"] = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect((10, 170), (300, 30)),
        text="Steps: 0",
        manager=manager,
    )

    return elements
