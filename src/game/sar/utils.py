import random

from minigrid.core.world_object import Lava

from .objects import FakeVictim, Victim


class VictimPlacer:
    """Handles placement of victims and fake victims."""

    DIRECTIONS = ["up", "down", "left", "right"]
    SHIFTS = ["left", "right"]

    def __init__(self, num_fake_victims=3, num_real_victims=1, important_victim="up"):
        """
        Initialize the victim placer.

        Args:
            num_fake_victims: Number of fake victims to place per room
            num_real_victims: Number of real victims to place per room
            important_victim: Direction of the important victim (placed in locked rooms)
        """
        self.num_fake_victims = num_fake_victims
        self.num_real_victims = num_real_victims
        # Can use either the factory or direct instantiation
        self.victims = {
            direction: Victim(direction, color="red") for direction in self.DIRECTIONS
        }
        self.important_victim = important_victim

    def place_fake_victims(self, level_gen, i, j):
        """Place fake victims in a room using factory pattern."""
        for _ in range(self.num_fake_victims):
            shift = random.choice(self.SHIFTS)
            direction = random.choice(self.DIRECTIONS)
            obj = FakeVictim(shift, direction, color="red")
            level_gen.place_in_room(i, j, obj)

    def place_all(self, level_gen, num_rows, num_cols):
        """Place victims and fake victims in all rooms."""
        for i in range(num_rows):
            for j in range(num_cols):
                room = level_gen.get_room(i, j)

                # Place real victims (num_real_victims per room)
                for _ in range(self.num_real_victims):
                    if room.locked:
                        # Always use important victim in locked rooms
                        victim_to_place = self.victims[self.important_victim]
                    else:
                        # Randomly select from non-important victims in unlocked rooms
                        non_important_victims = [
                            v for k, v in self.victims.items() if k != self.important_victim
                        ]
                        victim_to_place = random.choice(non_important_victims)

                    level_gen.place_in_room(i, j, victim_to_place)

                # Always place fake victims
                self.place_fake_victims(level_gen, i, j)


class LavaPlacer:
    """Handles placement of lava obstacles in the environment."""

    def __init__(self, lava_per_room=0, lava_probability=0.3):
        """
        Initialize lava placer.

        Args:
            lava_per_room: Fixed number of lava tiles per room (0 = use probability)
            lava_probability: Probability of placing lava in each room (used if lava_per_room=0)
        """
        self.lava_per_room = lava_per_room
        self.lava_probability = lava_probability

    def place_in_room(self, level_gen, i, j, num_lava=None):
        """
        Place lava tiles in a specific room.

        Args:
            level_gen: The level generator instance
            i: Room row index
            j: Room column index
            num_lava: Number of lava tiles to place (None = use lava_per_room)
        """
        if num_lava is None:
            num_lava = self.lava_per_room

        placed = 0
        max_attempts = 50  # Prevent infinite loops

        for _ in range(max_attempts):
            if placed >= num_lava:
                break

            try:
                level_gen.place_in_room(i, j, Lava())
                placed += 1
            except Exception:
                # Room might be full or placement failed
                continue

    def place_all(self, level_gen, num_rows, num_cols, skip_locked_rooms=False):
        """
        Place lava in all rooms based on configuration.

        Args:
            level_gen: The level generator instance
            num_rows: Number of room rows
            num_cols: Number of room columns
            skip_locked_rooms: If True, don't place lava in locked rooms
        """
        for i in range(num_rows):
            for j in range(num_cols):
                room = level_gen.get_room(i, j)

                # Skip locked rooms if requested
                if skip_locked_rooms and getattr(room, "locked", False):
                    continue

                # Decide whether to place lava in this room
                if self.lava_per_room > 0:
                    # Fixed number per room
                    self.place_in_room(level_gen, i, j, self.lava_per_room)
                elif random.random() < self.lava_probability:
                    # Random placement based on probability
                    num_lava = random.randint(1, 3)  # 1-3 lava tiles
                    self.place_in_room(level_gen, i, j, num_lava)
