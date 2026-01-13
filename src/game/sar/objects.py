from minigrid.core.constants import COLORS, IDX_TO_OBJECT, OBJECT_TO_IDX
from minigrid.core.world_object import WorldObj
from minigrid.utils.rendering import fill_coords, point_in_rect

# Register new objects
new_objects = [
    "victim_up",
    "victim_right",
    "victim_left",
    "fake_victim_left",
    "fake_victim_right",
]
for new_object in new_objects:
    if new_object not in OBJECT_TO_IDX:
        OBJECT_TO_IDX[new_object] = len(OBJECT_TO_IDX)
        IDX_TO_OBJECT[len(IDX_TO_OBJECT)] = new_object


class VictimBase(WorldObj):
    """Base class for all victim objects with common functionality."""

    # Rendering coordinates as (x1, x2, y1, y2) tuples
    # Subclasses should override this
    render_coords = []

    def can_overlap(self):
        """Victims cannot be walked over."""
        return False

    def can_pickup(self):
        """Victims can be picked up."""
        return True

    def render(self, img):
        """Render the victim using defined coordinates."""
        for coords in self.render_coords:
            fill_coords(img, point_in_rect(*coords), COLORS[self.color])
        return img


class VictimUp(VictimBase):
    """Victim facing upward."""

    render_coords = [
        (0.45, 0.55, 0.30, 0.80),  # Body vertical
        (0.25, 0.75, 0.30, 0.40),  # Arms horizontal
    ]

    def __init__(self, color="red"):
        super().__init__("victim_up", color)


class VictimLeft(VictimBase):
    """Victim facing left."""

    render_coords = [
        (0.20, 0.70, 0.45, 0.55),  # Body horizontal
        (0.20, 0.30, 0.25, 0.75),  # Arms vertical
    ]

    def __init__(self, color="red"):
        super().__init__("victim_left", color)


class VictimRight(VictimBase):
    """Victim facing right."""

    render_coords = [
        (0.30, 0.80, 0.45, 0.55),  # Body horizontal
        (0.70, 0.80, 0.25, 0.75),  # Arms vertical
    ]

    def __init__(self, color="red"):
        super().__init__("victim_right", color)


class FakeVictimLeft(VictimBase):
    """Fake victim (penalty when picked up) - left T shape."""

    render_coords = [
        (0.5, 0.6, 0.3, 0.8),  # Vertical line
        (0.40, 0.9, 0.3, 0.4),  # Horizontal top
    ]

    def __init__(self, type="fake_victim_left", color="red"):
        super().__init__(type, color)


class FakeVictimRight(VictimBase):
    """Fake victim (penalty when picked up) - right T shape."""

    render_coords = [
        (0.5, 0.6, 0.3, 0.8),  # Vertical line
        (0.2, 0.7, 0.3, 0.4),  # Horizontal top
    ]

    def __init__(self, type="fake_victim_right", color="red"):
        super().__init__(type, color)


# Constants for victim type checking (reduces duplication)
REAL_VICTIMS = (VictimUp, VictimRight, VictimLeft)
FAKE_VICTIMS = (FakeVictimLeft, FakeVictimRight)
ALL_VICTIMS = REAL_VICTIMS + FAKE_VICTIMS
