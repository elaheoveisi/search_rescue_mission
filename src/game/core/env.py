from __future__ import annotations

import numpy as np
import pygame
from minigrid.core.mission import MissionSpace
from minigrid.minigrid_env import MiniGridEnv


class SAREnv(MiniGridEnv):
    def __init__(
        self,
        grid_size=10,
        screen_size=1200,
        agent_start_pos=(1, 1),
        agent_start_dir=0,
        max_steps: int | None = None,
        **kwargs,
    ):
        self.agent_start_pos = agent_start_pos
        self.agent_start_dir = agent_start_dir

        mission_space = MissionSpace(mission_func=self._gen_mission)

        if max_steps is None:
            max_steps = 4 * grid_size**2

        super().__init__(
            mission_space=mission_space,
            grid_size=grid_size,
            max_steps=max_steps,
            **kwargs,
        )

        self.screen_size = screen_size

    @staticmethod
    def _gen_mission():
        return "grand mission"

    def render(self):
        # Set the desired resolution (higher than tile_size-based resolution)
        render_resolution = (
            self.screen_size
        )  # Could be user-defined or a constant like 1024

        # Get the base image (e.g. from the environment)
        frame = self.get_frame(
            self.highlight, self.tile_size, self.agent_pov
        )  # shape: (H, W, C)

        if self.render_mode == "rgb_array":
            return frame

        elif self.render_mode == "human":
            # Transpose to match Pygame's (width, height) format
            frame = np.transpose(frame, (1, 0, 2))  # (W, H, C)

            # Initialize rendering window once
            if self.window is None:
                pygame.init()
                pygame.display.init()
                self.window = pygame.display.set_mode(
                    (render_resolution, render_resolution)
                )
                pygame.display.set_caption("minigrid")

            # Initialize clock
            if self.clock is None:
                self.clock = pygame.time.Clock()

            # Convert frame to Pygame surface
            surface = pygame.surfarray.make_surface(frame)

            # High-resolution scaling
            upscale_surface = pygame.transform.smoothscale(
                surface, (render_resolution, render_resolution)
            )

            # Blit and update display
            self.window.blit(upscale_surface, (0, 0))
            pygame.display.flip()
            pygame.event.pump()
            self.clock.tick(self.metadata.get("render_fps", 30))
