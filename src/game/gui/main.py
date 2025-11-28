import numpy as np
import pygame
import pygame_gui

from .elements import generate_elements
from .user import User

pygame.init()


class SAREnvGUI:
    def __init__(self, env):
        self.window = None
        self.clock = None
        self.user = User(env)
        self.manager = pygame_gui.UIManager(
            (self.user.env.screen_size, self.user.env.screen_size)
        )
        self.running = True

        # Initialize the window and clock
        self._init_window()

        # Create GUI buttons for manual control
        self.elements = generate_elements(self.manager)

    def _init_window(self):
        """Initialize the Pygame window if it isn't already initialized."""
        if self.window is None:
            self.window = pygame.display.set_mode(
                (self.user.env.screen_size, self.user.env.screen_size)
            )
            pygame.display.set_caption("SAREnv")

        if self.clock is None:
            self.clock = pygame.time.Clock()

    def render(self, frame):
        # Get the environment frame and render it in Pygame
        frame = np.transpose(frame, (1, 0, 2))  # (W, H, C)
        surface = pygame.surfarray.make_surface(frame)
        surface = pygame.transform.smoothscale(
            surface, (self.user.env.screen_size, self.user.env.screen_size)
        )

        # Blit the surface to the window
        self.window.blit(surface, (0, 0))

        # Handle events and update GUI
        self.manager.update(1 / 60)  # Update the GUI elements
        self.manager.draw_ui(self.window)  # Draw the GUI elements
        pygame.display.update()

        # Limit the frame rate
        self.clock.tick(30)

    def reset(self):
        self.user.reset()

    def handle_gui_events(self, event):
        self.manager.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.elements["move_up_button"]:
                print("Hello World!")

    def handle_user_input(self, event):
        if event.type == pygame.KEYDOWN:
            event.key = pygame.key.name(int(event.key))
            self.user.handle_key(event)

    def close(self):
        self.running = False
        pygame.quit()

    def run(self):
        self.reset()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return

                # Handle gui and user input
                self.handle_gui_events(event)
                self.handle_user_input(event)

            frame = self.user.get_frame()
            self.render(frame)
