import math
import random

from minigrid.core.constants import COLOR_NAMES
from minigrid.core.grid import Grid
from minigrid.core.world_object import Ball, Door, Goal, Key, Lava, Wall

from .core.env import SAREnv
from .core.objects import SARVictim


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
        self.put_obj(SARVictim(), 2, 4)

        # Place the agent
        if self.agent_start_pos is not None:
            self.agent_pos = self.agent_start_pos
            self.agent_dir = self.agent_start_dir
        else:
            self.place_agent()

        self.mission = "Example"


class MultiRoomDifficultyEnv(SAREnv):
    def __init__(self, difficulty="easy", render_mode="human"):
        self.difficulty = difficulty
        self.room_size = 5

        if difficulty == "easy":
            self.room_count = 4
            self.locked_doors = 0
            self.add_lava = False
            self.max_steps = 80
        elif difficulty == "medium":
            self.room_count = 6
            self.locked_doors = 2
            self.add_lava = True
            self.max_steps = 150
        elif difficulty == "hard":
            self.room_count = 9
            self.locked_doors = 4
            self.add_lava = True
            self.max_steps = 200
        else:
            raise ValueError("Invalid difficulty level")

        # Compute grid dimensions based on room layout (rows × cols)
        self.rooms_per_row = math.ceil(math.sqrt(self.room_count))
        self.rooms_per_col = math.ceil(self.room_count / self.rooms_per_row)

        grid_width = self.rooms_per_row * (self.room_size - 1) + 1
        grid_height = self.rooms_per_col * (self.room_size - 1) + 1

        grid_size = max(grid_width, grid_height)

        super().__init__(
            grid_size=grid_size,
            max_steps=self.max_steps,
            see_through_walls=False,
            agent_view_size=7,
            render_mode=render_mode,
        )

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
                    self.grid.set(victim_x, victim_y, Ball("red"))

                room_idx += 1

        self.agent_pos = (1, 1)
        self.agent_dir = 0
        self.mission = f"Rescue the victim in a {self.difficulty} maze."
