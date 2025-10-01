# main.py
import argparse
import pyglet

from game import Game
from dual_view import main as run_dual  # dual-view launcher

def run_sar_mission_game(dual: bool):
    if dual:
        # Start the two-window (Pilot+Rescuer) mode
        run_dual()
    else:
        # Start the single-window mode (your existing Game class)
        game = Game()
        pyglet.app.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SAR Mission Game launcher")
    parser.add_argument("--dual", action="store_true",
                        help="Run in dual-view (Pilot+Rescuer) mode on one computer.")
    args = parser.parse_args()
    run_sar_mission_game(dual=args.dual)
