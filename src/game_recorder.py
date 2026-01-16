"""
Simple Game Recorder - saves grid as numeric array + action sequence.
"""

import pickle
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field


# Object type to integer mapping
OBJ_TO_ID = {
    None: 0,           # Empty
    "Wall": 1,
    "Door": 2,
    "Key": 3,
    "Lava": 4,
    "Victim": 5,
    "FakeVictim": 6,
}

ID_TO_OBJ = {v: k for k, v in OBJ_TO_ID.items()}


@dataclass
class GameRecording:
    """Minimal game recording."""
    timestamp: str = ""

    # Grid as numpy array (height x width) with object IDs
    grid: np.ndarray = None

    # Config
    config: dict = field(default_factory=dict)

    # Agent start
    agent_start_pos: tuple = (0, 0)
    agent_start_dir: int = 0

    # Action sequence
    actions: list = field(default_factory=list)
    rewards: list = field(default_factory=list)

    # Optional: frames
    frames: list = field(default_factory=list)


class GameRecorder:
    """Records game state."""

    ACTION_NAMES = ["left", "right", "forward", "pickup", "drop", "toggle", "done"]

    def __init__(self, env, record_frames=False):
        self.env = env
        self.record_frames = record_frames
        self.recording = None

    def _grid_to_array(self):
        """Convert grid to numeric numpy array."""
        arr = np.zeros((self.env.height, self.env.width), dtype=np.int8)
        for y in range(self.env.height):
            for x in range(self.env.width):
                obj = self.env.grid.get(x, y)
                if obj is not None:
                    obj_type = type(obj).__name__
                    arr[y, x] = OBJ_TO_ID.get(obj_type, 0)
        return arr

    def start(self):
        """Start recording after env.reset()."""
        self.recording = GameRecording(
            timestamp=datetime.now().isoformat(),
            grid=self._grid_to_array(),
            config={
                "room_size": self.env.room_size,
                "num_rows": self.env.num_rows,
                "num_cols": self.env.num_cols,
                "max_steps": getattr(self.env, "max_steps", 1000),
            },
            agent_start_pos=tuple(self.env.agent_pos),
            agent_start_dir=self.env.agent_dir,
        )
        if self.record_frames:
            self.recording.frames.append(self.env.render())

    def step(self, action, reward):
        """Record a step."""
        self.recording.actions.append(action)
        self.recording.rewards.append(reward)
        if self.record_frames:
            self.recording.frames.append(self.env.render())

    def save(self, filepath):
        """Save to pickle file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self.recording, f)
        print(f"Saved: {filepath}")


def load(filepath) -> GameRecording:
    """Load recording."""
    with open(filepath, "rb") as f:
        return pickle.load(f)


def print_grid(rec: GameRecording):
    """Print ASCII grid."""
    symbols = {0: ".", 1: "#", 2: "D", 3: "K", 4: "~", 5: "V", 6: "F"}
    h, w = rec.grid.shape

    print(f"\nGrid {w}x{h}:")
    for y in range(h):
        row = ""
        for x in range(w):
            if (x, y) == rec.agent_start_pos:
                row += "A"
            else:
                row += symbols.get(rec.grid[y, x], "?")
        print(row)
    print("Legend: .=empty #=wall D=door K=key ~=lava V=victim F=fake A=agent")


# Example
if __name__ == "__main__":
    from game.sar.env import PickupVictimEnv
    from game.sar.utils import VictimPlacer
    import random

    env = PickupVictimEnv(
        num_rows=2, num_cols=2,
        render_mode="rgb_array",
        victim_placer=VictimPlacer(num_fake_victims=3, num_real_victims=2),
    )

    rec = GameRecorder(env)
    env.reset()
    rec.start()

    for _ in range(20):
        action = random.randint(0, 5)
        obs, reward, term, trunc, _ = env.step(action)
        rec.step(action, reward)
        if term or trunc:
            break

    rec.save("recordings/demo.pkl")

    # Load and inspect
    data = load("recordings/demo.pkl")
    print(f"Grid shape: {data.grid.shape}")
    print(f"Actions: {len(data.actions)}")
    print(f"Total reward: {sum(data.rewards):.1f}")
    print_grid(data)
