from minigrid.envs.babyai.core.levelgen import LevelGen


class SARLevelGen(LevelGen):
    def __init__(
        self,
        room_size=8,
        num_rows=3,
        num_cols=3,
        num_dists=18,
        locked_room_prob=0.5,
        locations=True,
        unblocking=True,
        implicit_unlock=True,
        action_kinds=["goto", "pickup", "open", "putnext"],
        instr_kinds=["action", "and", "seq"],
        **kwargs,
    ):
        super().__init__(
            room_size,
            num_rows,
            num_cols,
            num_dists,
            locked_room_prob,
            locations,
            unblocking,
            implicit_unlock,
            action_kinds,
            instr_kinds,
            **kwargs,
        )
