from .objects import FakeVictimLeft, FakeVictimRight, Victim


class BaseAction:
    """Abstract base class for all actions."""

    def __init__(self, env):
        self.env = env

    def execute(self):
        raise NotImplementedError


class RescueAction(BaseAction):
    """Pick up a victim (reward +1) or fake victim (penalty -0.5)."""

    def execute(self):
        fwd_pos = self.env.front_pos
        obj = self.env.grid.get(*fwd_pos)
        reward = 0

        if isinstance(obj, Victim):
            self.env.grid.set(*fwd_pos, None)
            self.env.saved_victims += 1
            reward = 1.0
        elif isinstance(obj, (FakeVictimLeft, FakeVictimRight)):
            self.env.grid.set(*fwd_pos, None)
            reward = -0.5
        else:
            # fallback to normal pickup
            return self.env.step(self.env.actions.pickup)

        obs = self.env.gen_obs()
        terminated = self.env.saved_victims == self.env.num_rows * self.env.num_cols
        return obs, reward, terminated, False, {}
