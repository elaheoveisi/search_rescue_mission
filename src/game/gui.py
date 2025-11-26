import numpy as np
import pygame
import pygame_gui
from minigrid.manual_control import ManualControl

pygame.init()


class SAREnvGUI:
    def __init__(self, env):
        self.env = env  # SAREnv instance as a member of the GUI class
        self.window = None
        self.clock = None
        self.closed = False
        self.manual_control = ManualControl(self.env)
        self.manager = pygame_gui.UIManager(
            (self.env.screen_size, self.env.screen_size)
        )
        self.running = True

        # Initialize the window and clock
        self._init_window()

        # Create GUI buttons for manual control
        self.move_up_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 10), (100, 50)),
            text="Move Up",
            manager=self.manager,
        )

        self.move_down_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((120, 10), (100, 50)),
            text="Move Down",
            manager=self.manager,
        )

        self.move_left_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((10, 70), (100, 50)),
            text="Move Left",
            manager=self.manager,
        )

        self.move_right_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((120, 70), (100, 50)),
            text="Move Right",
            manager=self.manager,
        )

        self.reward_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 130), (300, 30)),
            text="Reward: 0",
            manager=self.manager,
        )

        self.step_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((10, 170), (300, 30)),
            text="Steps: 0",
            manager=self.manager,
        )

    def _init_window(self):
        """Initialize the Pygame window if it isn't already initialized."""
        if self.window is None:
            self.window = pygame.display.set_mode(
                (self.env.screen_size, self.env.screen_size)
            )
            pygame.display.set_caption("SAREnv")

        if self.clock is None:
            self.clock = pygame.time.Clock()

    def render(self, frame):
        # Get the environment frame and render it in Pygame
        frame = np.transpose(frame, (1, 0, 2))  # (W, H, C)
        surface = pygame.surfarray.make_surface(frame)
        surface = pygame.transform.smoothscale(
            surface, (self.env.screen_size, self.env.screen_size)
        )

        # Blit the surface to the window
        self.window.blit(surface, (0, 0))

        # Handle events and update GUI
        self.manager.update(1 / 60)  # Update the GUI elements
        self.manager.draw_ui(self.window)  # Draw the GUI elements
        pygame.display.update()

        # Limit the frame rate
        self.clock.tick(30)

    def run(self):
        self.manual_control.reset()
        while not self.closed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.env.close()
                    break
                if event.type == pygame.KEYDOWN:
                    event.key = pygame.key.name(int(event.key))
                    self.manual_control.key_handler(event)
                    frame = self.env.render()
                    self.render(frame)
