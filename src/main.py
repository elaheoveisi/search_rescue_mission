import pygame
import yaml
from minigrid.manual_control import ManualControl

from game.core.camera import FullviewCamera
from game.gui.main import SAREnvGUI
from game.sar.env import CombinedInstructionEnv
from game.sar.utils import VictimPlacer
from game.test_environments import MultiRoomDifficultyEnv, TestEnv
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
    victim_placer = VictimPlacer(num_fake_victims=3, important_victim="up")
    env = CombinedInstructionEnv(
        num_rows=3,
        num_cols=3,
        screen_size=800,
        render_mode="rgb_array",
        agent_pov=True,
        add_lava=True,
        lava_per_room=1,
        camera_strategy=FullviewCamera(),
        victim_placer=victim_placer,
    )
    gui = SAREnvGUI(env)
    gui.run()
