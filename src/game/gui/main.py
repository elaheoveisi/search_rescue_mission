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

        self.panel_width = 375
        self.window_size = (self.env_size + self.panel_width, self.env_size)

        self.window = env.window
        self.fullscreen = fullscreen

        if self.window is None:
            display_flags = pygame.FULLSCREEN if self.fullscreen else 0
            if self.fullscreen:
                # Get the actual display size for fullscreen
                self.window = pygame.display.set_mode((0, 0), display_flags)
                self.screen_size = self.window.get_size()
            else:
                self.window = pygame.display.set_mode(self.window_size, display_flags)
                self.screen_size = self.window_size

        # Calculate offsets to center the game content
        self._calculate_offsets()

        # Initialize UI manager with theme
        self.manager = pygame_gui.UIManager(self.window_size, "src/game/gui/theme.json")

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
        self.info_panel = InfoPanel(self.manager, self.env_size, self.panel_width)
        self.info_panel.env_size = info_panel_height  # Update to half height

        # Create chat panel (bottom half)
        chat_y_position = info_panel_height
        self.chat_panel = ChatPanel(
            self.manager,
            self.env_size,
            chat_y_position,
            self.panel_width,
            chat_panel_height,
        )

    def _calculate_offsets(self):
        """Calculate offsets and scale to center and fit the game content on screen."""
        # Calculate scale factor to fit the screen while maintaining aspect ratio
        scale_x = self.screen_size[0] / self.window_size[0]
        scale_y = self.screen_size[1] / self.window_size[1]
        self.scale = min(scale_x, scale_y)

        # Calculate scaled dimensions
        self.scaled_width = int(self.window_size[0] * self.scale)
        self.scaled_height = int(self.window_size[1] * self.scale)

        # Calculate offsets to center the scaled content
        self.offset_x = (self.screen_size[0] - self.scaled_width) // 2
        self.offset_y = (self.screen_size[1] - self.scaled_height) // 2

    def _init_window(self):
        """Initialize the Pygame window if it isn't already initialized."""
        if self.window is None:
            pygame.display.set_caption("SAREnv")

        if self.clock is None:
            self.clock = pygame.time.Clock()

    def render(self, frame):
        # Fill the screen with black (for fullscreen centering)
        self.window.fill((0, 0, 0))

        # Create a combined surface for game + UI
        combined_surface = pygame.Surface(self.window_size, pygame.SRCALPHA)

        # Get the environment frame and render it in Pygame
        frame = np.transpose(frame, (1, 0, 2))  # (W, H, C)
        game_surface = pygame.surfarray.make_surface(frame)
        game_surface = pygame.transform.smoothscale(
            game_surface, (self.user.env.screen_size, self.user.env.screen_size)
        )

        # Blit the game surface to the combined surface
        combined_surface.blit(game_surface, (0, 0))

        # Update panel data (pygame_gui handles drawing)
        self.info_panel.render(self.user.env)
        self.chat_panel.render()

        # Update and draw the UI manager on the combined surface
        time_delta = self.clock.tick(30) / 1000.0
        self.manager.update(time_delta)
        self.manager.draw_ui(combined_surface)

        # Scale the combined surface and blit to window with offset
        if self.scale != 1.0:
            scaled_surface = pygame.transform.smoothscale(
                combined_surface, (self.scaled_width, self.scaled_height)
            )
            self.window.blit(scaled_surface, (self.offset_x, self.offset_y))
        else:
            self.window.blit(combined_surface, (self.offset_x, self.offset_y))

        # Update display
        pygame.display.update()

    def reset(self):
        self.user.reset()

    def handle_gui_events(self, event):
        self.manager.process_events(event)

    def handle_user_input(self, event):
        if event.type == pygame.KEYDOWN:
            # Quit with ESC or Q
            if event.key == pygame.K_ESCAPE:
                self.close()
            # Toggle fullscreen with F11
            elif event.key == pygame.K_F11:
                self.toggle_fullscreen()
            else:
                event.key = pygame.key.name(int(event.key))
                self.user.handle_key(event)

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            # Get the actual display size for fullscreen
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.screen_size = self.window.get_size()
        else:
            self.window = pygame.display.set_mode(self.window_size)
            self.screen_size = self.window_size

        # Recalculate offsets for centering
        self._calculate_offsets()

        # Recreate the UI manager with new window
        self.manager = pygame_gui.UIManager(self.window_size, "theme.json")

        # Recreate panels with new manager
        info_panel_height = self.env_size // 2
        chat_panel_height = self.env_size // 2
        chat_y_position = info_panel_height

        self.info_panel = InfoPanel(self.manager, self.env_size, self.panel_width)
        self.info_panel.env_size = info_panel_height

        self.chat_panel = ChatPanel(
            self.manager,
            self.env_size,
            chat_y_position,
            self.panel_width,
            chat_panel_height,
        )

    def close(self):
        self.running = False

    def run(self):
        self.reset()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    break

                # Handle gui and user input
                self.handle_gui_events(event)
                self.handle_user_input(event)

            # Only render if still running
            if self.running:
                frame = self.user.get_frame()
                self.render(frame)

        # Clean up pygame after loop exits
        pygame.quit()
