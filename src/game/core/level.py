import random

import numpy as np
import pygame
from minigrid.envs.babyai.core.levelgen import LevelGen

from .objects import FakeVictimLeft, FakeVictimRight, Victim


class SARLevelGen(LevelGen):
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
        **kwargs,
    ):
        self.num_fake_victims = num_fake_victims
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

    def place_fake_victims(self, i, j):
        # Place fake victimes
        for k in range(self.num_fake_victims):
            if random.random() <= 0.5:
                obj = FakeVictimLeft(color="red")
            else:
                obj = FakeVictimRight(color="red")
            self.place_in_room(i, j, obj)

    def place_victims_and_distractors(self):
        # Get room dimensions
        rooms = [(i, j) for i in range(self.num_rows) for j in range(self.num_cols)]

        # Ensure at least one victim in each room
        for i, j in rooms:
            self.place_in_room(i, j, Victim(color="red"))  # Place victim in the room
            self.place_fake_victims(i, j)

    def gen_mission(self):
        # Optional: blocked areas instead of locked rooms
        if self._rand_bool():
            self.add_locked_room()  # interpret as rubble-blocked area

        self.connect_all()

        self.place_victims_and_distractors()

        while True:
            self.place_agent()
            start_room = self.room_from_pos(*self.agent_pos)
            # Ensure that we are not placing the agent in the locked room
            if start_room is self.locked_room:
                continue
            break

        # If no unblocking required, make sure all objects are
        # reachable without unblocking
        if not self.unblocking:
            self.check_objs_reachable()

        # Generate random instructions
        self.instrs = self.rand_instr(
            action_kinds=self.action_kinds,
            instr_kinds=self.instr_kinds,
        )

    def get_agent_centered_crop(self, extra_tiles=(4, 4), tile_size=None):
        """
        Returns a pixel crop of the grid centered on the agent.

        Args:
            extra_tiles: (extra_width, extra_height) number of tiles to add around the agent's room
            tile_size: pixels per tile
        Returns:
            cropped_img: np.ndarray RGB image
        """
        tile_size = tile_size or 32
        agent_x, agent_y = self.agent_pos

        # Get agent's room
        room = self.room_from_pos(agent_x, agent_y)
        room_x, room_y = room.top
        room_w, room_h = room.size

        # Define the bounding box in tiles
        width_tiles = room_w + extra_tiles[0]
        height_tiles = room_h + extra_tiles[1]

        # Center bounding box on agent
        top_x = agent_x - width_tiles // 2
        top_y = agent_y - height_tiles // 2

        # Clip to grid bounds
        top_x = max(0, min(top_x, self.width - width_tiles))
        top_y = max(0, min(top_y, self.height - height_tiles))

        # Bottom-right corner
        bot_x = top_x + width_tiles
        bot_y = top_y + height_tiles

        # Convert to pixels
        px_min = top_x * tile_size
        px_max = bot_x * tile_size
        py_min = top_y * tile_size
        py_max = bot_y * tile_size

        # Render full grid
        full_img = self.grid.render(
            tile_size,
            self.agent_pos,
            self.agent_dir,
            highlight_mask=None,
        )

        # Crop pixels
        cropped_img = full_img[py_min:py_max, px_min:px_max, :]

        return cropped_img

    def render(self):
        img = self.get_agent_centered_crop()
        if self.render_mode == "human":
            # Pygame expects (width, height, channels)
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
