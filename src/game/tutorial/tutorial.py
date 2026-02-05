"""Simple tutorial module for the SAR game.

This provides a tiny demo function to be expanded with
interactive tutorial steps later.
"""

def tutorial_demo():
    """Run a minimal tutorial demo."""
    print("SAR Tutorial: basic actions and navigation demo.")
    return {"status": "ok", "message": "Tutorial ran successfully."}


if __name__ == "__main__":
    tutorial_demo()


# New: single-room SAR environment helpers
try:
    from minigrid.core.world_object import Door

    from ..sar.env import PickupVictimEnv
    from ..sar.utils import VictimPlacer, LavaPlacer
    from ..sar.instructions import PickupAllVictimsInstr
    from ..sar.objects import Victim, FakeVictim, REAL_VICTIMS, FAKE_VICTIMS


    class OneRoomOpenDoorEnv(PickupVictimEnv):
        """One-room environment: 1 real victim, 1 fake victim, and an open door."""

        def __init__(self, **kwargs):
            vp = VictimPlacer(num_fake_victims=1, num_real_victims=1)
            super().__init__(num_rows=1, num_cols=1, victim_placer=vp, **kwargs)

        def gen_mission(self):
            # Connect the single room and place the agent
            self.connect_all()
            self.place_agent()

            # Optionally add lava (none by default)
            if getattr(self, "add_lava", False):
                self.lava_placer.place_in_room(self, 0, 0, num_lava=0)

            # Place victims into the single room
            self.victim_placer.place_all(self, 1, 1)

            # Place an open door on any internal wall if possible; otherwise
            # fall back to placing a Door object inside the room (visual only)
            room = self.get_room(0, 0)
            for door_idx, neighbor in enumerate(room.neighbors):
                try:
                    # Try to add a proper room door (works when neighbor exists)
                    if room.door_pos[door_idx] is not None and neighbor is not None:
                        door, _ = self.add_door(0, 0, door_idx, locked=False)
                        door.is_open = True
                        break
                except Exception:
                    pass

            else:
                # No valid inter-room door available; place a Door object inside
                try:
                    d = Door("green", is_locked=False)
                    d.is_open = True
                    self.place_in_room(0, 0, d)
                except Exception:
                    pass

            victims = self.get_all_victims()
            self.instrs = PickupAllVictimsInstr(victims)


    class OneRoomYellowKeyFireEnv(PickupVictimEnv):
        """One-room environment: fake + real victims, yellow door, yellow + red keys, and fire."""

        def __init__(self, **kwargs):
            # keep a few fake victims and one real victim
            vp = VictimPlacer(num_fake_victims=3, num_real_victims=1)
            super().__init__(num_rows=1, num_cols=1, victim_placer=vp, add_lava=True, lava_per_room=2, **kwargs)

        def gen_mission(self):
            # Connect and place agent
            self.connect_all()
            self.place_agent()

            # Add some fire (lava) into the room
            if getattr(self, "add_lava", False):
                self.lava_placer.place_in_room(self, 0, 0, num_lava=2)

            # Place victims
            self.victim_placer.place_all(self, 1, 1)

            # Add a yellow door (closed) on an internal wall if possible; otherwise
            # place a yellow Door inside the room
            room = self.get_room(0, 0)
            for door_idx, neighbor in enumerate(room.neighbors):
                try:
                    if room.door_pos[door_idx] is not None and neighbor is not None:
                        door, _ = self.add_door(0, 0, door_idx, locked=False)
                        try:
                            door.color = "yellow"
                        except Exception:
                            pass
                        break
                except Exception:
                    pass
            else:
                try:
                    d = Door("yellow", is_locked=False)
                    self.place_in_room(0, 0, d)
                except Exception:
                    pass

            # Place keys inside the room (demo: both yellow and red keys are present)
            try:
                self.add_object(0, 0, "key", "yellow")
                self.add_object(0, 0, "key", "red")
            except Exception:
                # Fallback to placing keys via place_in_room if add_object not available
                try:
                    self.place_in_room(0, 0, self._create_obj("key", "yellow"))
                    self.place_in_room(0, 0, self._create_obj("key", "red"))
                except Exception:
                    pass

            victims = self.get_all_victims()
            self.instrs = PickupAllVictimsInstr(victims)


    class OneRoomFakeOnlyEnv(PickupVictimEnv):
        """One-room environment: only fake victims and a closed red door."""

        def __init__(self, **kwargs):
            vp = VictimPlacer(num_fake_victims=4, num_real_victims=0)
            super().__init__(num_rows=1, num_cols=1, victim_placer=vp, add_lava=False, **kwargs)

        def gen_mission(self):
            self.connect_all()
            self.place_agent()

            # Place only fake victims
            self.victim_placer.place_all(self, 1, 1)

            # Add a closed red door on an internal wall if possible; otherwise
            # place a red Door inside the room
            room = self.get_room(0, 0)
            for door_idx, neighbor in enumerate(room.neighbors):
                try:
                    if room.door_pos[door_idx] is not None and neighbor is not None:
                        door, _ = self.add_door(0, 0, door_idx, locked=False)
                        try:
                            door.color = "red"
                        except Exception:
                            pass
                        break
                except Exception:
                    pass
            else:
                try:
                    d = Door("red", is_locked=False)
                    self.place_in_room(0, 0, d)
                except Exception:
                    pass

            victims = self.get_all_victims()
            # Use the same pickup instruction; with zero real victims this will be trivial
            self.instrs = PickupAllVictimsInstr(victims)

    MINIGRID_AVAILABLE = True
except Exception:
    MINIGRID_AVAILABLE = False
    OneRoomOpenDoorEnv = None
    OneRoomYellowKeyFireEnv = None
    OneRoomFakeOnlyEnv = None


# Runtime workaround: monkeypatch LavaPlacer to tolerate swapped (i,j) ordering
# when `level_gen.get_room(i, j)` raises AssertionError (index-order bug).
if MINIGRID_AVAILABLE:
    try:
        import random

        from ..sar import utils as sar_utils

        if hasattr(sar_utils, "LavaPlacer"):
            LP = sar_utils.LavaPlacer
            _orig_place_in_room = LP.place_in_room
            _orig_place_all = LP.place_all

            def _patched_place_in_room(self, level_gen, i, j, num_lava=None):
                try:
                    return _orig_place_in_room(self, level_gen, i, j, num_lava=num_lava)
                except AssertionError:
                    # Retry with swapped indices if underlying API expects (col, row)
                    return _orig_place_in_room(self, level_gen, j, i, num_lava=num_lava)

            def _patched_place_all(self, level_gen, num_rows, num_cols, skip_locked_rooms=False):
                try:
                    return _orig_place_all(self, level_gen, num_rows, num_cols, skip_locked_rooms=skip_locked_rooms)
                except AssertionError:
                    # Fall back to a safe iteration that tries both index orders
                    for i in range(num_rows):
                        for j in range(num_cols):
                            try:
                                room = level_gen.get_room(i, j)
                            except AssertionError:
                                try:
                                    room = level_gen.get_room(j, i)
                                except Exception:
                                    # Give up on this room
                                    continue

                            if skip_locked_rooms and getattr(room, "locked", False):
                                continue

                            if self.lava_per_room > 0:
                                _patched_place_in_room(self, level_gen, i, j, self.lava_per_room)
                            elif random.random() < self.lava_probability:
                                n = random.randint(1, 3)
                                _patched_place_in_room(self, level_gen, i, j, n)

            LP.place_in_room = _patched_place_in_room
            LP.place_all = _patched_place_all
    except Exception:
        # Non-fatal: if monkeypatching fails, leave original behavior
        pass

    # Also monkeypatch VictimPlacer to tolerate swapped (i,j) ordering
    try:
        from ..sar import utils as sar_utils

        if hasattr(sar_utils, "VictimPlacer"):
            VP = sar_utils.VictimPlacer
            _orig_place_fake_victims = VP.place_fake_victims
            _orig_place_all_v = VP.place_all

            def _safe_place(level_gen, a, b, obj):
                try:
                    level_gen.place_in_room(a, b, obj)
                except Exception:
                    try:
                        level_gen.place_in_room(b, a, obj)
                    except Exception:
                        raise

            def _patched_place_fake_victims(self, level_gen, i, j):
                for _ in range(self.num_fake_victims):
                    shift = random.choice(self.SHIFTS)
                    direction = random.choice(self.DIRECTIONS)
                    obj = FakeVictim(shift, direction, color="red")
                    try:
                        _safe_place(level_gen, i, j, obj)
                    except Exception:
                        # skip placement if both orders fail
                        continue

            def _patched_place_all(self, level_gen, num_rows, num_cols, *args, **kwargs):
                for i in range(num_rows):
                    for j in range(num_cols):
                        # Try primary ordering, fall back to swapped ordering
                        try:
                            room = level_gen.get_room(i, j)
                            ii, jj = i, j
                        except AssertionError:
                            try:
                                room = level_gen.get_room(j, i)
                                ii, jj = j, i
                            except Exception:
                                # Can't get room in either ordering; skip
                                continue

                        # Place real victims
                        for _ in range(self.num_real_victims):
                            if getattr(room, "locked", False):
                                victim_to_place = self.victims[self.important_victim]
                            else:
                                non_important_victims = [v for k, v in self.victims.items() if k != self.important_victim]
                                victim_to_place = random.choice(non_important_victims)
                            try:
                                _safe_place(level_gen, ii, jj, victim_to_place)
                            except Exception:
                                pass

                        # Place fake victims using patched helper
                        _patched_place_fake_victims(self, level_gen, ii, jj)

            VP.place_fake_victims = _patched_place_fake_victims
            VP.place_all = _patched_place_all
    except Exception:
        pass
