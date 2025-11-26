import yaml
from minigrid.manual_control import ManualControl

from game.custom_env import MultiRoomDifficultyEnv, TestEnv
from game.gui import SAREnvGUI
from utils import skip_run

# Load config
config_path = "configs/config.yml"
with open(config_path, "r") as file:
    config = yaml.safe_load(file)


with skip_run("skip", "minigrid_sar") as check, check():
    env = TestEnv(render_mode="human")

    # enable manual control for testing
    manual_control = ManualControl(env, seed=42)
    manual_control.start()


with skip_run("skip", "minigrid_sar") as check, check():
    env = MultiRoomDifficultyEnv(difficulty="hard", render_mode="human")

    # enable manual control for testing
    manual_control = ManualControl(env, seed=42)
    manual_control.start()


with skip_run("run", "minigrid_sar") as check, check():
    env = MultiRoomDifficultyEnv(difficulty="hard", render_mode="rgb_array")

    gui = SAREnvGUI(env)  # Pass SAREnv as a composition
    gui.run()
