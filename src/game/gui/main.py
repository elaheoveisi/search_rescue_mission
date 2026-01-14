import numpy as np
import pygame
import pygame_gui

from .chat import ChatPanel
from .info import InfoPanel
from .user import User

pygame.init()


class SAREnvGUI:
    def __init__(self, env, fullscreen=False):
        self.user = User(env)
        self.env_size = self.user.env.screen_size

        self.panel_width = 400
        self.window_size = (self.env_size + self.panel_width, self.env_size)
        self.manager = pygame_gui.UIManager(self.window_size)
        self.window = env.window
        self.fullscreen = fullscreen

        if self.window is None:
            display_flags = pygame.FULLSCREEN if self.fullscreen else 0
            self.window = pygame.display.set_mode(self.window_size, display_flags)

        self.running = True
        self.clock = None

        # Initialize the window and clock
        self._init_window()

        # Split the right panel in half
        # Top half: Info panel
        # Bottom half: Chat panel
        info_panel_height = self.env_size // 2
        chat_panel_height = self.env_size // 2

        # Create info panel for displaying game statistics (top half)
        self.info_panel = InfoPanel(self.env_size, self.panel_width)
        self.info_panel.env_size = info_panel_height  # Update to half height

        # Create chat panel (bottom half)
        chat_y_position = info_panel_height
        self.chat_panel = ChatPanel(
            self.env_size, chat_y_position, self.panel_width, chat_panel_height
        )

    def _init_window(self):
        """Initialize the Pygame window if it isn't already initialized."""
        if self.window is None:
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

        # Render info panel (top half) with current game state
        self.info_panel.render(self.window, self.user.env)

        # Render chat panel (bottom half)
        self.chat_panel.render(self.window)

        # Handle events and update GUI
        self.manager.update(1 / 60)  # Update the GUI elements
        pygame.display.update()

        # Limit the frame rate
        self.clock.tick(30)

    def reset(self):
        self.user.reset()

    def handle_gui_events(self, event):
        self.manager.process_events(event)

    def handle_user_input(self, event):
        if event.type == pygame.KEYDOWN:
            # Toggle fullscreen with F11
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            else:
                event.key = pygame.key.name(int(event.key))
                self.user.handle_key(event)

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode(self.window_size, pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(self.window_size)

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
