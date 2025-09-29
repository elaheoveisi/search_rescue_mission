# main.py
import pyglet, argparse
from game import Game



def run_sar_mission_game():
    game = Game()
    pyglet.app.run()

if __name__ == "__main__":
    run_sar_mission_game()

