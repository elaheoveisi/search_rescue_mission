import random

from ..core.level import SARLevelGen
from .actions import RescueAction
from .instructions import PickupAllVictimsInstr
from .objects import REAL_VICTIMS
from .utils import LavaPlacer


class CombinedInstructionEnv(SARLevelGen):
    def __init__(
        self,
        room_size=8,
        num_rows=3,
        num_cols=3,
        num_dists=18,
        unblocking=False,
        add_lava=True,
        lava_per_room=0,
        lava_probability=0.5,
        victim_placer=None,
        **kwargs,
    ):
        # We add many distractors to increase the probability
        # of ambiguous locations within the same room
        super().__init__(
            room_size=room_size,
            num_rows=num_rows,
            num_cols=num_cols,
            num_dists=num_dists,
            locations=False,
            unblocking=unblocking,  # Configurable: False ensures all victims are reachable
            implicit_unlock=False,
            **kwargs,
        )
        self.victim_placer = victim_placer

        # Lava configuration
        self.add_lava = add_lava
        if add_lava:
            self.lava_placer = LavaPlacer(
                lava_per_room=lava_per_room, lava_probability=lava_probability
            )

        # Custom actions
        self.resuce_action = RescueAction(self)
        self.saved_victims = 0

    def add_locked_rooms(self, n_locked):
        added = 0

        while added < n_locked:
            # Pick a random room
            i, j = self._rand_int(0, self.num_cols), self._rand_int(0, self.num_rows)
            locked_room = self.get_room(i, j)

            # Skip if room is already locked
            if locked_room.locked:
                continue

            # Find all door indices that are still empty
            empty_doors = [idx for idx, d in enumerate(locked_room.doors) if d is None]
            if not empty_doors:
                continue  # no free door, pick another room

            # Pick a random empty door
            door_idx = random.choice(empty_doors)

            # Skip if door leads outside
            if locked_room.neighbors[door_idx] is None:
                continue

            # Add locked door
            door, _ = self.add_door(i, j, door_idx, locked=True)
            locked_room.locked = True

            # Place key in a different room
            while True:
                ki, kj = (
                    self._rand_int(0, self.num_cols),
                    self._rand_int(0, self.num_rows),
                )
                key_room = self.get_room(ki, kj)
                if key_room is locked_room:
                    continue
                if getattr(key_room, "locked", False):
                    continue  # avoid placing key in another locked room
                self.add_object(ki, kj, "key", door.color)
                break

            added += 1

    def _count_objects_by_type(self, obj_types):
        """
        Utility method to count objects of specific types on the grid.

        Args:
            obj_types: Tuple of object types to count

        Returns:
            int: Number of objects matching the types
        """
        count = 0
        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid.get(x, y)
                if isinstance(obj, obj_types):
                    count += 1
        return count

    def _find_objects_by_type(self, obj_types):
        """
        Utility method to find all objects of specific types on the grid.

        Args:
            obj_types: Tuple of object types to find

        Returns:
            list: List of objects matching the types
        """
        objects = []
        for x in range(self.width):
            for y in range(self.height):
                obj = self.grid.get(x, y)
                if isinstance(obj, obj_types):
                    objects.append(obj)
        return objects

    def get_all_victims(self):
        """
        Returns a list of all victim objects currently present in the environment.
        """
        return self._find_objects_by_type(REAL_VICTIMS)

    def get_mission_status(self):
        """
        Returns the current mission status.

        Returns:
            dict: Dictionary containing:
                - 'status': 'success', 'failure', or 'incomplete'
                - 'saved_victims': Number of victims saved
                - 'total_victims': Total number of victims in the mission
                - 'remaining_victims': Number of victims left to save
        """
        if hasattr(self, "instrs") and self.instrs is not None:
            status = self.instrs.verify(self)
        else:
            status = "incomplete"

        # Count remaining victims on the grid
        remaining_victims = len(self.get_all_victims())

        return {
            "status": status,
            "saved_victims": self.saved_victims,
            "remaining_victims": remaining_victims,
        }

    def validate_instrs(self, instrs):
        """
        Override to handle custom instruction types.

        Args:
            instrs: Instruction object to validate
        """
        # Allow our custom PickupAllVictimsInstr without validation
        if isinstance(instrs, PickupAllVictimsInstr):
            return

        # Fall back to parent validation for standard instructions
        super().validate_instrs(instrs)

    def num_navs_needed(self, instrs):
        """
        Override to handle custom instruction types.

        Args:
            instrs: Instruction object

        Returns:
            int: Number of navigation actions needed (for mission generation)
        """
        # For PickupAllVictimsInstr, return number of victims
        if isinstance(instrs, PickupAllVictimsInstr):
            return instrs.num_victims

        # Fall back to parent method for standard instructions
        return super().num_navs_needed(instrs)

    def gen_mission(self):
        """Generate the mission layout and instructions."""

        # Add locked rooms
        n_locked = int(self.num_cols * self.num_rows * 0.5)  # or pass as argument
        self.add_locked_rooms(n_locked)

        self.connect_all()

        # Place agent outside locked room
        while True:
            self.place_agent()
            start_room = self.room_from_pos(*self.agent_pos)
            if not start_room.locked:
                break

        # Add lava obstacles (before victims to avoid blocking them)
        if self.add_lava:
            self.lava_placer.place_all(self, self.num_rows, self.num_cols)

        # Add victims
        self.victim_placer.place_all(self, self.num_rows, self.num_cols)

        # Check that all objects (including victims) are reachable from agent start position
        if not self.unblocking:
            self.check_objs_reachable()

        victims = self.get_all_victims()

        # Create instruction to pick up all victims
        self.instrs = PickupAllVictimsInstr(victims)

    def _step(self, action):
        return super().step(action)

    def step(self, action):
        if action == self.actions.pickup:
            obs, reward, terminated, truncated, info = self.resuce_action.execute(
                action
            )

            # Verify if mission is complete after pickup action
            if hasattr(self, "instrs") and self.instrs is not None:
                status = self.instrs.verify(action)
                if status == "success":
                    terminated = True
                    reward += 1.0  # Bonus reward for completing mission
                    info["mission_complete"] = True

            return obs, reward, terminated, truncated, info
        else:
            return self._step(action)
