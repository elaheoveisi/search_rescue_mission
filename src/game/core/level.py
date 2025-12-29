import random

import numpy as np
import pygame
from minigrid.envs.babyai.core.levelgen import LevelGen

from .actions import RescueAction
from .camera import CameraStrategy, EdgeFollowCamera
from .objects import FakeVictimLeft, FakeVictimRight, Victim


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
        self.saved_victims = 0

        # Custom actions
        self.resuce_action = RescueAction(self)

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

    def _extended_pickup(self):
        fwd_pos = self.front_pos
        obj = self.grid.get(*fwd_pos)

        # Fallback to normal pickup if not a victim
        if not isinstance(obj, (Victim, FakeVictimLeft, FakeVictimRight)):
            return super().step(self.actions.pickup)

        # Remove object from grid
        self.grid.set(*fwd_pos, None)

        # Assign reward
        if isinstance(obj, Victim):
            reward = 1.0
            self.saved_victims += 1
        else:  # Fake victim
            reward = -0.5

        # Generate observation
        obs = self.gen_obs()

        # Check if all victims are saved
        terminated = self.saved_victims == self.num_rows * self.num_cols

        return obs, reward, terminated, False, {}

    def step(self, action):
        if action == self.actions.pickup:
            return self.resuce_action.execute()
        else:
            return super().step(action)

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
