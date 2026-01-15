import pygame
import yaml

from game.gui.main import SAREnvGUI
from game.sar.env import PickupVictimEnv
from game.sar.utils import VictimPlacer
from utils import skip_run

# Load config
config_path = "configs/config.yml"
with open(config_path, "r") as file:
    config = yaml.safe_load(file)


with skip_run("run", "sar_gui_advanced") as check, check():
    # Access the width and height of the current display
    screen_height = pygame.display.Info().current_h
    victim_placer = VictimPlacer(num_fake_victims=5, important_victim="down")
    env = PickupVictimEnv(
        num_rows=3,
        num_cols=3,
        screen_size=800,
        render_mode="rgb_array",
        agent_pov=True,
        add_lava=True,
        lava_per_room=2,
        locked_room_prob=0.5,
        # camera_strategy=FullviewCamera(),
        tile_size=64,
        victim_placer=victim_placer,
    )
    gui = SAREnvGUI(env, fullscreen=True)
    gui.run()
