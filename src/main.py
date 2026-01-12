import pygame
import yaml
from minigrid.manual_control import ManualControl

from game.custom_env import CombinedInstructionEnv, MultiRoomDifficultyEnv, TestEnv
from game.gui.main import SAREnvGUI
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
    env = MultiRoomDifficultyEnv(
        config=config["difficulties"]["hard"], render_mode="human"
    )

    # enable manual control for testing
    manual_control = ManualControl(env, seed=42)
    manual_control.start()

with skip_run("skip", "sar_gui") as check, check():
    env = MultiRoomDifficultyEnv(
        config=config["game_difficulties"]["hard"],
        render_mode="rgb_array",
        tile_size=64,
    )
    gui = SAREnvGUI(env)
    gui.run()

with skip_run("run", "sar_gui_advanced") as check, check():
    # Access the width and height of the current display
    screen_height = pygame.display.Info().current_h
    env = CombinedInstructionEnv(
        num_rows=3,
        num_cols=3,
        screen_size=800,
        render_mode="rgb_array",
        agent_pov=True,
        # camera_strategy=FullviewCamera(),
    )
    gui = SAREnvGUI(env)
    gui.run()
