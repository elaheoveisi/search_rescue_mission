from minigrid.core.constants import IDX_TO_OBJECT, OBJECT_TO_IDX
from minigrid.core.world_object import WorldObj
from minigrid.utils.rendering import (
    fill_coords,
    point_in_rect,
)

# Register new objects
new_objects = ["victim"]
for new_object in new_objects:
    # Register new object type before using it
    if new_object not in OBJECT_TO_IDX:
        OBJECT_TO_IDX[new_object] = len(OBJECT_TO_IDX)
        IDX_TO_OBJECT[len(IDX_TO_OBJECT)] = new_object


class SARVictim(WorldObj):
    def __init__(self):
        super().__init__("victim", "red")

    def can_overlap(self):
        return False

    def can_pickup(self):
        return True

    def render(self, img):
        # Draw upright T
        fill_coords(img, point_in_rect(0.45, 0.55, 0.2, 0.8), (255, 0, 0))
        fill_coords(img, point_in_rect(0.25, 0.75, 0.2, 0.3), (255, 0, 0))
        return img
