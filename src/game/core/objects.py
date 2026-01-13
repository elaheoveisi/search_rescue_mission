from minigrid.core.constants import COLORS, IDX_TO_OBJECT, OBJECT_TO_IDX
from minigrid.core.world_object import WorldObj
from minigrid.utils.rendering import (
    fill_coords,
    point_in_rect,
)

# Register new objects
new_objects = [
    "victim_up",
    "victim_right",
    "victim_left",
    "fake_victim_left",
    "fake_victim_right",
]
for new_object in new_objects:
    # Register new object type before using it
    if new_object not in OBJECT_TO_IDX:
        OBJECT_TO_IDX[new_object] = len(OBJECT_TO_IDX)
        IDX_TO_OBJECT[len(IDX_TO_OBJECT)] = new_object


class VictimUp(WorldObj):
    def __init__(self, color="red"):
        super().__init__("victim_up", color)

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        fill_coords(img, point_in_rect(0.45, 0.55, 0.30, 0.80), COLORS[self.color])
        fill_coords(img, point_in_rect(0.25, 0.75, 0.30, 0.40), COLORS[self.color])

        return img


class VictimLeft(WorldObj):
    def __init__(self, color="red"):
        super().__init__("victim_left", color)

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        fill_coords(img, point_in_rect(0.20, 0.70, 0.45, 0.55), COLORS[self.color])
        fill_coords(img, point_in_rect(0.20, 0.30, 0.25, 0.75), COLORS[self.color])
        return img


class VictimRight(WorldObj):
    def __init__(self, color="red"):
        super().__init__("victim_right", color)

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        fill_coords(img, point_in_rect(0.30, 0.80, 0.45, 0.55), COLORS[self.color])
        fill_coords(img, point_in_rect(0.70, 0.80, 0.25, 0.75), COLORS[self.color])

        return img


class FakeVictimLeft(WorldObj):
    def __init__(self, type="fake_victim_left", color="red"):
        super().__init__(type, color)

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        # Draw upright T
        fill_coords(img, point_in_rect(0.5, 0.6, 0.3, 0.8), COLORS[self.color])
        fill_coords(img, point_in_rect(0.40, 0.9, 0.3, 0.4), COLORS[self.color])
        return img


class FakeVictimRight(WorldObj):
    def __init__(self, type="fake_victim_right", color="red"):
        super().__init__(type, color)

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        # Draw upright T
        fill_coords(img, point_in_rect(0.5, 0.6, 0.3, 0.8), COLORS[self.color])
        fill_coords(img, point_in_rect(0.2, 0.7, 0.3, 0.4), COLORS[self.color])
        return img
