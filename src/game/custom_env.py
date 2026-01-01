import math
import random

import pygame
from minigrid.core.constants import COLOR_NAMES
from minigrid.core.grid import Grid
from minigrid.core.world_object import Door, Goal, Key, Lava, Wall

from .core.env import SAREnv
from .core.level import SARLevelGen
from .core.objects import FakeVictimLeft, Victim


class TestEnv(SAREnv):
    def _gen_grid(self, width, height):
        # Create an empty grid
        self.grid = Grid(width, height)

        # Generate the surrounding walls
        self.grid.wall_rect(0, 0, width, height)

        # Generate vertical separation wall
        for i in range(0, height):
            self.grid.set(5, i, Wall())

        # Place the door and key
        self.grid.set(5, 6, Door(COLOR_NAMES[0], is_locked=True))
        self.grid.set(3, 6, Key(COLOR_NAMES[0]))

        # Place a goal square in the bottom-right corner
        self.put_obj(Goal(), width - 2, height - 2)
        self.put_obj(Victim(), 2, 4)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "Example"


class MultiRoomDifficultyEnv(SAREnv):
    def __init__(self, config, render_mode="human", **kwargs):
        self.room_size = 5
        self.step_count = 0

        # Configuration
        self.room_count = config["room_count"]
        self.locked_doors = config["locked_doors"]
        self.add_lava = config["add_lava"]
        self.max_steps = config["max_steps"]

        # Compute grid dimensions based on room layout (rows × cols)
        self.rooms_per_row = math.ceil(math.sqrt(self.room_count))
        self.rooms_per_col = math.ceil(self.room_count / self.rooms_per_row)

        grid_width = self.rooms_per_row * (self.room_size - 1) + 1
        grid_height = self.rooms_per_col * (self.room_size - 1) + 1

        grid_size = max(grid_width, grid_height)

        # TODO: Add a condition to run in windowed mode
        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        print(self.window)

        super().__init__(
            grid_size=grid_size,
            max_steps=self.max_steps,
            see_through_walls=False,
            agent_view_size=7,
            render_mode=render_mode,
            window=self.window,
            **kwargs,
        )

    def _randomly_remove_walls(self, removal_prob=0.1):
        """
        Randomly removes interior walls (not boundary walls).
        removal_prob: probability of removing each wall.
        """
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                obj = self.grid.get(x, y)

                # Remove only plain walls (not doors, lava, keys, etc.)
                if isinstance(obj, Door):
                    if random.random() < removal_prob:
                        self.grid.set(x, y, None)
                        self.grid.set(x, y + 1, None)
                        self.grid.set(x, y - 1, None)
                        self.grid.set(x - 1, y, None)
                        self.grid.set(x + 1, y, None)

    def _gen_grid(self, width, height):
        self.grid = Grid(width, height)
        self.grid.wall_rect(0, 0, width, height)

        room_idx = 0
        locked_doors_added = 0

        for row in range(self.rooms_per_col):
            for col in range(self.rooms_per_row):
                if room_idx >= self.room_count:
                    break

                xL = col * (self.room_size - 1)
                yT = row * (self.room_size - 1)

                # Draw room walls
                self.grid.wall_rect(xL, yT, self.room_size, self.room_size)

                # Connect to the left room
                if col > 0 and room_idx > 0:
                    door_x = xL
                    door_y = yT + self.room_size // 2
                    is_locked = False

                    if locked_doors_added < self.locked_doors:
                        is_locked = True
                        locked_doors_added += 1
                        # Key goes in left room
                        key_x = (
                            xL
                            - (self.room_size - 1)
                            + random.randint(1, self.room_size - 2)
                        )
                        key_y = door_y
                        self.grid.set(key_x, key_y, Key("yellow"))

                    self.grid.set(door_x, door_y, Door("yellow", is_locked=is_locked))

                # Connect to the room above
                if row > 0:
                    door_x = xL + self.room_size // 2
                    door_y = yT
                    self.grid.set(door_x, door_y, Door("yellow", is_locked=False))

                # Add lava
                if self.add_lava and room_idx % 2 == 0:
                    lava_x = xL + random.randint(1, self.room_size - 2)
                    lava_y = yT + random.randint(1, self.room_size - 2)
                    self.grid.set(lava_x, lava_y, Lava())

                # Add victim in the last room
                if room_idx == self.room_count - 1:
                    victim_x = xL + self.room_size // 2
                    victim_y = yT + self.room_size // 2
                    self.grid.set(victim_x, victim_y, FakeVictimLeft(color="red"))

                room_idx += 1

        self._randomly_remove_walls()

        self.agent_pos = (1, 1)
        self.agent_dir = 0
        self.mission = "Rescue the victim in a maze."


class CombinedInstructionEnv(SARLevelGen):
    def __init__(self, room_size=8, num_rows=3, num_cols=3, num_dists=18, **kwargs):
        # We add many distractors to increase the probability
        # of ambiguous locations within the same room
        super().__init__(
            room_size=room_size,
            num_rows=num_rows,
            num_cols=num_cols,
            num_dists=num_dists,
            locations=False,
            unblocking=True,
            implicit_unlock=False,
            **kwargs,
        )

    def gen_mission(self):
        """Generate the mission layout and instructions."""
        if self._rand_float(0, 1) <= 0:
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
