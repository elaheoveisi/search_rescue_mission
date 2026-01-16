from minigrid.envs.babyai.core.verifier import Instr

from .objects import REAL_VICTIMS


def calculate_max_steps(
    room_size: int,
    num_rows: int,
    num_cols: int,
    num_doors: int,
    victims_per_room: int,
    human_exploration_factor: float = 0.5,
    steps_per_victim: int = 5,
    safety_buffer: float = 1.0,
):
    """
    Calculate a human-friendly max step limit for a MiniGrid-style environment.

    Parameters
    ----------
    room_size : int
        Size of one room (room_size x room_size).
    grid_rows : int
        Number of room rows.
    grid_cols : int
        Number of room columns.
    num_doors : int
        Total number of doors in the maze.
    victims_per_room : int
        Number of real victims per room.
    human_exploration_factor : float
        Multiplier for human inefficiency (default = 2.0).
    steps_per_victim : int
        Extra steps to approach + rescue one victim.
    safety_buffer : float
        Final multiplicative slack for mistakes and hesitation.

    Returns
    -------
    int
        Recommended max_steps.
    """

    num_rooms = num_rows * num_cols

    # 1. Human exploration cost per room
    nav_time_room = human_exploration_factor * (room_size**2)

    # 2. Base exploration of all rooms
    exploration_cost = num_rooms * nav_time_room

    # 3. Door & key backtracking cost
    # Each door ≈ one extra room traversal
    door_cost = num_doors * nav_time_room

    # 4. Victim rescue cost
    total_victims = num_rooms * victims_per_room
    victim_cost = total_victims * steps_per_victim

    # 5. Total before buffer
    raw_steps = exploration_cost + door_cost + victim_cost

    # 6. Safety buffer for human mistakes
    max_steps = int(raw_steps * safety_buffer)

    return max_steps


class PickupAllVictimsInstr(Instr):
    """
    Instruction to pick up all victims in the environment.
    This instruction verifies that all victims have been picked up (removed from grid).
    """

    def __init__(self, victims):
        """
        Initialize instruction with list of victim objects to pick up.

        Args:
            victims: List of victim objects that need to be picked up
        """
        self.victims = victims
        self.victim_types = [type(v) for v in victims]
        self.num_victims = len(victims)

    def verify(self, action):
        """
        Verify if all victims have been picked up.

        Args:
            env: The environment instance

        Returns:
            str: 'success' if all victims picked up, 'continue' otherwise
        """
        # Use utility method to count remaining victims
        remaining_victims = self.env._count_objects_by_type(REAL_VICTIMS)

        # All victims have been picked up
        if remaining_victims == 0:
            return "success"

        # Still victims to pick up
        return "continue"

    def surface(self, env):
        """
        Return a natural language description of the instruction.

        Args:
            env: The environment instance

        Returns:
            str: Description of the instruction
        """
        return f"pick up all {self.num_victims} victims"
