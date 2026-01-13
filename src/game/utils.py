import random

from game.core.objects import (
    FakeVictimLeft,
    FakeVictimRight,
    VictimLeft,
    VictimRight,
    VictimUp,
)


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
                level_gen.place_in_room(
                    i,
                    j,
                    random.choice(
                        [
                            VictimUp(color="red"),
                            VictimRight(color="red"),
                            VictimLeft(color="red"),
                        ]
                    ),
                )
                self.place_fake_victims(level_gen, i, j)
