import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pygame
from minigrid.envs.babyai.core.levelgen import LevelGen

from .objects import FakeVictimLeft, FakeVictimRight, Victim


@dataclass
class CameraConfig:
    """Configuration for camera behavior."""

    view_tiles: Tuple[int, int] = (12, 12)
    margin: int = 3
    tile_size: int = 32


class CameraStrategy(ABC):
    """Abstract base class for different camera behaviors."""

    @abstractmethod
    def get_crop(self, grid, agent_pos, agent_dir, **kwargs) -> np.ndarray:
        """Return a cropped view of the grid."""
        pass


class AgentCenteredCamera(CameraStrategy):
    """Camera that stays centered on the agent's room."""

    def __init__(self, extra_tiles=(4, 4), tile_size=32):
        self.extra_tiles = extra_tiles
        self.tile_size = tile_size

    def get_crop(self, grid, agent_pos, agent_dir, room=None, **kwargs) -> np.ndarray:
        """Get a crop centered on the agent's current room."""
        agent_x, agent_y = agent_pos
        room_w, room_h = room.size

        width_tiles = room_w + self.extra_tiles[0]
        height_tiles = room_h + self.extra_tiles[1]

        top_x = agent_x - width_tiles // 2
        top_y = agent_y - height_tiles // 2

        top_x = max(0, min(top_x, grid.width - width_tiles))
        top_y = max(0, min(top_y, grid.height - height_tiles))

        bot_x = top_x + width_tiles
        bot_y = top_y + height_tiles

        px_min, px_max = top_x * self.tile_size, bot_x * self.tile_size
        py_min, py_max = top_y * self.tile_size, bot_y * self.tile_size

        full_img = grid.render(
            self.tile_size, agent_pos, agent_dir, highlight_mask=None
        )
        return full_img[py_min:py_max, px_min:px_max, :]


class EdgeFollowCamera(CameraStrategy):
    """Camera that follows the agent with a dead-zone margin."""

    def __init__(self, config: CameraConfig = None):
        self.config = config or CameraConfig()
        self.top_x = 0
        self.top_y = 0
        self.initialized = False

    def _initialize(self, agent_x, agent_y):
        """Initialize camera position."""
        view_w, view_h = self.config.view_tiles
        self.top_x = max(0, agent_x - view_w // 2)
        self.top_y = max(0, agent_y - view_h // 2)
        self.initialized = True

    def _update_position(self, agent_x, agent_y, grid_width, grid_height):
        """Update camera position based on agent movement."""
        if not self.initialized:
            self._initialize(agent_x, agent_y)

        view_w, view_h = self.config.view_tiles
        margin = self.config.margin

        # Calculate dead-zone boundaries
        left = self.top_x + margin
        right = self.top_x + view_w - margin - 1
        top = self.top_y + margin
        bottom = self.top_y + view_h - margin - 1

        # Move camera if agent exits dead-zone
        if agent_x < left:
            self.top_x -= left - agent_x
        elif agent_x > right:
            self.top_x += agent_x - right

        if agent_y < top:
            self.top_y -= top - agent_y
        elif agent_y > bottom:
            self.top_y += agent_y - bottom

        # Clamp to grid bounds
        self.top_x = max(0, min(self.top_x, grid_width - view_w))
        self.top_y = max(0, min(self.top_y, grid_height - view_h))

    def get_crop(
        self, grid, agent_pos, agent_dir, grid_width=None, grid_height=None, **kwargs
    ) -> np.ndarray:
        """Get a crop that follows the agent with edge-following behavior."""
        agent_x, agent_y = agent_pos
        self._update_position(agent_x, agent_y, grid_width, grid_height)

        view_w, view_h = self.config.view_tiles
        tile_size = self.config.tile_size

        # Render full grid
        full_img = grid.render(tile_size, agent_pos, agent_dir, highlight_mask=None)

        # Calculate pixel boundaries
        px_min = self.top_x * tile_size
        px_max = (self.top_x + view_w) * tile_size
        py_min = self.top_y * tile_size
        py_max = (self.top_y + view_h) * tile_size

        return full_img[py_min:py_max, px_min:px_max, :]

    def reset(self):
        """Reset camera state."""
        self.initialized = False


class VictimPlacer:
    """Handles placement of victims and fake victims."""

    def __init__(self, num_fake_victims=3):
        self.num_fake_victims = num_fake_victims

    def place_fake_victims(self, level_gen, i, j):
        """Place fake victims in a room."""
        for _ in range(self.num_fake_victims):
            obj = (
                FakeVictimLeft(color="red")
                if random.random() <= 0.5
                else FakeVictimRight(color="red")
            )
            level_gen.place_in_room(i, j, obj)

    def place_all(self, level_gen, num_rows, num_cols):
        """Place victims and fake victims in all rooms."""
        for i in range(num_rows):
            for j in range(num_cols):
                level_gen.place_in_room(i, j, Victim(color="red"))
                self.place_fake_victims(level_gen, i, j)


class SARLevelGen(LevelGen):
    """Search and Rescue level generator with pluggable camera system."""

    def __init__(
        self,
        num_fake_victims=3,
        room_size=8,
        num_rows=3,
        num_cols=3,
        num_dists=18,
        locked_room_prob=0.5,
        locations=True,
        unblocking=True,
        implicit_unlock=True,
        action_kinds=["goto", "pickup", "open", "putnext"],
        instr_kinds=["action", "and", "seq"],
        window=None,
        camera_strategy=None,
        **kwargs,
    ):
        if window is None:
            self.window = pygame.display.set_mode([800, 800])

        super().__init__(
            room_size,
            num_rows,
            num_cols,
            num_dists,
            locked_room_prob,
            locations,
            unblocking,
            implicit_unlock,
            action_kinds,
            instr_kinds,
            **kwargs,
        )

        # Use strategy pattern for camera
        self.camera = camera_strategy or EdgeFollowCamera()
        self.victim_placer = VictimPlacer(num_fake_victims)

    def gen_mission(self):
        """Generate the mission layout and instructions."""
        if self._rand_bool():
            self.add_locked_room()

        self.connect_all()
        self.victim_placer.place_all(self, self.num_rows, self.num_cols)

        # Place agent outside locked room
        while True:
            self.place_agent()
            start_room = self.room_from_pos(*self.agent_pos)
            if start_room is not self.locked_room:
                break

        if not self.unblocking:
            self.check_objs_reachable()

        self.instrs = self.rand_instr(
            action_kinds=self.action_kinds,
            instr_kinds=self.instr_kinds,
        )

    def get_camera_view(self, **kwargs) -> np.ndarray:
        """Get current camera view using the configured strategy."""
        room = self.room_from_pos(*self.agent_pos)
        return self.camera.get_crop(
            grid=self.grid,
            agent_pos=self.agent_pos,
            agent_dir=self.agent_dir,
            room=room,
            grid_width=self.width,
            grid_height=self.height,
            **kwargs,
        )

    def render(self):
        """Render the environment."""
        img = self.get_camera_view()

        if self.render_mode == "human":
            img = np.transpose(img, axes=(1, 0, 2))

            if self.window is None:
                pygame.init()
                pygame.display.init()
                self.window = pygame.display.set_mode(
                    (self.screen_size, self.screen_size)
                )

            surf = pygame.surfarray.make_surface(img)
            surf = pygame.transform.smoothscale(
                surf, (self.screen_size, self.screen_size)
            )

            self.window.blit(surf, (0, 0))
            pygame.event.pump()
            pygame.display.flip()

        elif self.render_mode == "rgb_array":
            return img

    def switch_camera(self, camera_strategy: CameraStrategy):
        """Switch to a different camera strategy at runtime."""
        self.camera = camera_strategy
