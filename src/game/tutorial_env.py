"""Wrapper factory for tutorial environments.

Provides a `TutorialEnv` factory function that returns one of the
single-room tutorial environments implemented in `game.tutorial.tutorial`.
"""
from .tutorial.tutorial import (
    OneRoomOpenDoorEnv,
    OneRoomYellowKeyFireEnv,
    OneRoomFakeOnlyEnv,
)
from game.sar.utils import VictimPlacer
from game.sar.objects import Victim, FakeVictim
from game.sar.instructions import PickupAllVictimsInstr
from minigrid.core.world_object import Door
from game.sar.env import PickupVictimEnv
from game.core.camera import AgentCenteredCamera


class TutorialSequenceEnv(PickupVictimEnv):
    """Three-room sequential tutorial environment.

    Rooms (left to right):
      0 - first tutorial: 1 real + 1 fake, open door to room1
      1 - second tutorial: fake + real victims, yellow locked door to room2, keys and fire
      2 - third tutorial: fake victims only

    `start_part` selects which room the agent starts in (1-3).
    """

    def __init__(self, start_part: int = 1, **kwargs):
        # Create a 1x3 layout so doors connect naturally
        # Provide a VictimPlacer instance so PickupVictimEnv.reset() can compute steps
        tile_size = kwargs.get("tile_size", 64)
        vp = VictimPlacer(num_fake_victims=3, num_real_victims=1)
        super().__init__(num_rows=1, num_cols=3, victim_placer=vp, **kwargs)
        # Use an agent-centered camera with no extra tiles so only the current room is shown
        try:
            self.camera = AgentCenteredCamera(extra_tiles=(0, 0), tile_size=tile_size)
        except Exception:
            pass
        self.start_part = max(1, min(3, start_part))


class TutorialCompletionInstr:
    """Tutorial-specific instruction that only completes when the tutorial
    has been explicitly marked finished (e.g., after entering the final room).

    This prevents picking up victims from auto-completing the tutorial.
    """

    def __init__(self, total_parts: int = 3):
        self.total_parts = total_parts

    def verify(self, env):
        # The env will set `_tutorial_finished = True` when the final room is reached
        if getattr(env, "_tutorial_finished", False):
            return "success"
        return "continue"

    def surface(self, env):
        return "complete the tutorial (reach the final room)"

    def gen_mission(self):
        # Ensure rooms are created
        self.connect_all()

        # Place agent in the chosen start room
        start_i = self.start_part - 1
        self.place_agent(i=start_i, j=0)

        # Prepare templates for room contents (factories) and only populate start room
        self.room_templates = [
            [lambda: Victim("up"), lambda: FakeVictim("left", "up")],
            [lambda: FakeVictim("left", "down"), lambda: FakeVictim("left", "down"), lambda: FakeVictim("left", "down"), lambda: Victim("down")],
            [lambda: FakeVictim("right", "left"), lambda: FakeVictim("right", "left"), lambda: FakeVictim("right", "left"), lambda: FakeVictim("right", "left")],
        ]

        # Ensure doors exist between consecutive rooms (0-1 and 1-2)
        try:
            # door 0->1 (right wall of room 0)
            if not self.get_room(0, 0).doors[0]:
                door_obj, _ = self.add_door(0, 0, 0, locked=False)
                try:
                    # ensure door is closed (set multiple attributes for compatibility)
                    door_obj.is_open = False
                    door_obj.open = False
                    door_obj.locked = False
                    door_obj.is_locked = False
                except Exception:
                    pass
        except Exception:
            pass

        try:
            # door 1->2 (right wall of room 1)
            # make this door locked and require the blue key
            if not self.get_room(1, 0).doors[0]:
                door_obj, _ = self.add_door(1, 0, 0, color="blue", locked=True)
                try:
                    door_obj.color = "blue"
                except Exception:
                    pass
                try:
                    # set lock/open attributes broadly for compatibility
                    door_obj.locked = True
                except Exception:
                    pass
                try:
                    door_obj.is_locked = True
                except Exception:
                    pass
                try:
                    door_obj.is_open = False
                except Exception:
                    pass
                try:
                    door_obj.open = False
                except Exception:
                    pass
        except Exception:
            pass

        # Populate only the starting room
        self.clear_room(0)
        self.clear_room(1)
        self.clear_room(2)
        self.populate_room(start_i)

        # Tutorial completion instruction: do not auto-complete on pickups
        self._tutorial_finished = False
        self.instrs = TutorialCompletionInstr(total_parts=3)

    def populate_room(self, i: int):
        """Place template objects into room i."""
        if not (0 <= i < len(self.room_templates)):
            return
        for factory in self.room_templates[i]:
            try:
                self.place_in_room(i, 0, factory())
            except Exception:
                pass

        # Special placements for room1: keys and lava
        if i == 1:
            # Ensure a blue key is placed in room 1 so the locked blue door can be opened
            try:
                try:
                    # Prefer add_object (places a proper key object)
                    self.add_object(1, 0, "key", "blue")
                except Exception:
                    try:
                        key_obj = self._create_obj("key", "blue")
                        self.place_in_room(1, 0, key_obj)
                    except Exception:
                        pass
            except Exception:
                pass
            if getattr(self, "add_lava", False):
                try:
                    self.lava_placer.place_in_room(self, 1, 0, num_lava=2)
                except Exception:
                    pass
        # Ensure door objects remain closed/locked after adding objects
        try:
            self._normalize_doors()
        except Exception:
            pass

    def clear_room(self, i: int):
        """Remove all objects from room i (grid cells + room.objs list)."""
        try:
            room = self.get_room(i, 0)
        except Exception:
            return
        # Clear objects from grid
        for obj in list(room.objs):
            try:
                pos = getattr(obj, "cur_pos", None)
                if pos:
                    self.grid.set(pos[0], pos[1], None)
            except Exception:
                pass
        room.objs.clear()

    def step(self, action):
        """Intercept open actions to transition room contents when a door is opened."""
        # If pickup action, choose behavior depending on what's in front:
        # - If a key is in the front cell, let the base environment handle pickup
        #   so the key is collected into the agent inventory.
        # - Otherwise, use the rescue action to pick up victims without triggering
        #   the parent's mission-complete auto-advance.
        if action == self.actions.pickup:
            try:
                front = self.grid.get(*self.front_pos)
            except Exception:
                front = None

            if front is not None and getattr(front, "type", None) == "key":
                return self._step(action)

            try:
                obs, reward, terminated, truncated, info = self.resuce_action.execute(action)
                return obs, reward, terminated, truncated, info
            except Exception:
                return self._step(action)

        # Detect if the action is the door-toggle and the front cell is a door
        is_open_action = action == self.actions.toggle
        front_obj = self.grid.get(*self.front_pos)

        # Execute the base step (opens doors, moves agent, etc.)
        obs, reward, terminated, truncated, info = super().step(action)

        if is_open_action and front_obj is not None and front_obj.type == "door":
            # Find which door index this corresponds to in the current room
            room = self.room_from_pos(*self.agent_pos)
            door_idx = None
            for idx, pos in enumerate(room.door_pos):
                if pos is not None and tuple(pos) == tuple(self.front_pos):
                    door_idx = idx
                    break

            if door_idx is not None:
                neighbor = room.neighbors[door_idx]
                if neighbor is not None:
                    # clear current room and populate neighbor room
                    cur_i = self.room_from_pos(*self.agent_pos).top[0] // (self.room_size - 1)
                    # compute neighbor index i based on neighbor.top
                    neigh_i = neighbor.top[0] // (self.room_size - 1)
                    try:
                        self.clear_room(cur_i)
                        self.populate_room(neigh_i)
                        # normalize doors after populating the next room
                        try:
                            self._normalize_doors()
                        except Exception:
                            pass
                        # Update internal victim list for bookkeeping (do not replace instrs)
                        try:
                            self.current_victims = self.get_all_victims()
                        except Exception:
                            pass
                        # If we've just moved into the third room (index 2), mark tutorial finished
                        if neigh_i == 2:
                            try:
                                self._tutorial_finished = True
                            except Exception:
                                pass
                            # signal finish in the returned info tuple
                            info = info or {}
                            info["tutorial_finished"] = True
                    except Exception:
                        pass

        return obs, reward, terminated, truncated, info

    def get_camera_view(self, **kwargs):
        """Return a crop showing only the agent's current room.

        This forces the GUI to display a single room at a time for the tutorial.
        """
        # Compute the room-aligned top-left using room_size to ensure a single room
        tile_size = getattr(self.camera, "tile_size", 32)

        # room tile width/height in tiles (rooms overlap walls by 1, so room step is room_size - 1)
        step = self.room_size - 1
        agent_x, agent_y = self.agent_pos
        room_i = agent_x // step
        room_j = agent_y // step

        top_x = room_i * step
        top_y = room_j * step

        room_w = self.room_size
        room_h = self.room_size

        px_min = top_x * tile_size
        px_max = (top_x + room_w) * tile_size
        py_min = top_y * tile_size
        py_max = (top_y + room_h) * tile_size

        full_img = self.grid.render(tile_size, self.agent_pos, self.agent_dir, highlight_mask=None)
        return full_img[py_min:py_max, px_min:px_max, :]

    def _normalize_doors(self):
        """Scan the grid and ensure door objects are closed/locked as intended.

        Locks doors colored 'blue' and leaves others unlocked. Also forces
        doors to `is_open=False` to avoid unintended open state.
        """
        for x in range(self.width):
            for y in range(self.height):
                try:
                    obj = self.grid.get(x, y)
                except Exception:
                    obj = None
                if obj is None:
                    continue
                typ = getattr(obj, "type", None)
                if typ == "door":
                    try:
                        # Force closed
                        obj.is_open = False
                    except Exception:
                        pass
                    try:
                        obj.open = False
                    except Exception:
                        pass
                    # Enforce lock state by color
                    color = getattr(obj, "color", None)
                    if color == "blue":
                        try:
                            obj.locked = True
                        except Exception:
                            pass
                        try:
                            obj.is_locked = True
                        except Exception:
                            pass
                    else:
                        try:
                            obj.locked = False
                        except Exception:
                            pass
                        try:
                            obj.is_locked = False
                        except Exception:
                            pass


def TutorialEnv(start_part: int = 1, **kwargs):
    """Factory returning the sequential tutorial environment instance.

    Keeps API compatible with previous `TutorialEnv(start_part=...)` usage.
    """
    return TutorialSequenceEnv(start_part=start_part, **kwargs)


def _room_crop_frame(env, tile_size: int):
    # Compute crop aligned to a single room using env.room_size
    step = env.room_size - 1
    agent_x, agent_y = env.agent_pos
    room_i = agent_x // step
    room_j = agent_y // step
    top_x = room_i * step
    top_y = room_j * step
    room_w = env.room_size
    room_h = env.room_size
    full_img = env.grid.render(tile_size, env.agent_pos, env.agent_dir, highlight_mask=None)
    px_min = top_x * tile_size
    px_max = (top_x + room_w) * tile_size
    py_min = top_y * tile_size
    py_max = (top_y + room_h) * tile_size
    return full_img[py_min:py_max, px_min:px_max, :]


def _get_frame_method(self, highlight, tile_size, agent_pov):
    try:
        return _room_crop_frame(self, tile_size)
    except Exception:
        # Fallback to superclass behavior
        return super(TutorialSequenceEnv, self).get_camera_view()


# Attach get_frame to the class so SAREnv.render uses the room-only crop
setattr(TutorialSequenceEnv, "get_frame", _get_frame_method)


    # Backwards-compatible alias (if something imports TutorialEnv as a class)

