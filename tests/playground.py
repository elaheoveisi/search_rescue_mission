from minigrid.envs.babyai.core.levelgen import LevelGen
from minigrid.manual_control import ManualControl


class CombinedInstructionEnv(LevelGen):
    def __init__(self, room_size=8, num_rows=3, num_cols=3, num_dists=18, **kwargs):
        # We add many distractors to increase the probability
        # of ambiguous locations within the same room
        super().__init__(
            room_size=room_size,
            num_rows=num_rows,
            num_cols=num_cols,
            num_dists=num_dists,
            locations=False,
            unblocking=True,
            implicit_unlock=False,
            window=self.window,
            **kwargs,
        )


env = CombinedInstructionEnv(
    num_rows=4, num_cols=4, instr_kinds=["seq", "seq"], render_mode="human"
)
print(env.get_instructions())

obs = env.reset()
done = False
while not done:
    manual_control = ManualControl(env, seed=46)
    manual_control.start()
