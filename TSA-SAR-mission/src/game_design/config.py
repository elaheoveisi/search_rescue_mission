# config.py
import pyglet

# Window & grid
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 800
CELL_SIZE = 20
SIDEBAR_W = 380
PLAY_W_PX = WINDOW_WIDTH - SIDEBAR_W

GRID_W = WINDOW_WIDTH // CELL_SIZE
GRID_H = WINDOW_HEIGHT // CELL_SIZE
PLAY_W = PLAY_W_PX // CELL_SIZE
PLAY_H = GRID_H

# Time & zoom
TIME_LIMIT = 900
MIN_ZOOM = 0.25
MAX_ZOOM = 3.0
ZOOM_STEP = 0.10

# Colors
COLOR_BG = (22, 24, 28)
COLOR_GRID = (55, 60, 70)
COLOR_WALL = (90, 100, 115)
# Colors
COLOR_BG = (22, 24, 28)
COLOR_GRID = (55, 60, 70)
COLOR_WALL = (90, 100, 115)

COLOR_WALL_ORANGE = (255, 165, 0)  
COLOR_PLAYER = (60, 200, 255)
WALL_CLEARANCE = 2
WALL_ORANGE_PCT   = 0.25
MULTI_WALL_PCT    = 0.15
MULTI_WALL_LAYERS = (1, 2)
COLOR_WALL_ORANGE = (255, 165, 0)
MULTI_WALL_GROW_PCT  = 0.25 

MIN_PASSABLE_RATIO  = 0.50  
RED_SECTORS_X = 2   # split map into 3 columns
RED_SECTORS_Y = 2  # and 2 rows → 6 sectors total
WALL_SEGMENT_LEN = (3, 11)
WALL_ATTEMPTS_PER_SEG = 30          # vertical sector count for balancing
RED_DIFFICULTY_DIST_WEIGHT = 1.0    # weight for normalized BFS distance
RED_DIFFICULTY_DEADEND_BONUS = 0.8  # add if tile is a dead-end (degree==1)
RED_DIFFICULTY_CORRIDOR_BONUS = 0.4 # add if tile is a corridor (degree==2 & straight)
RED_DIFFICULTY_NEARWALL_BONUS = 0.2 # add if ≥2 blocked sides




COLOR_PLAYER = (60, 200, 255)

COLOR_PANEL_RGB = (10, 10, 14)
COLOR_PANEL_ALPHA = 220
COLOR_PANEL_BORDER = (140, 100, 220)

COLOR_TEXT = (230, 230, 240, 255)
COLOR_PURPLE = (190, 140, 255)
COLOR_YELLOW = (255, 227, 102)
COLOR_RED = (230, 70, 70)
COLOR_RESCUE = (255, 220, 60)

# Victims
NUM_RED = 15
NUM_PURPLE = 30
NUM_YELLOW = 45
RED_SEP_CELLS = 10      # minimum Chebyshev distance between red victims
RED_FAR_QUANTILE = 0.3  # pick reds from the farthest 35% of cells (65th percentile+)

PROTECTED_CELLS = [(5, 5), (10, 8), (12, 15)]  


# Distribution for purple & yellow (sector-based)
PURPLE_SECTORS_X = 9
PURPLE_SECTORS_Y = 9
YELLOW_SECTORS_X = 9
YELLOW_SECTORS_Y = 9

# Start pos
START = (9, 9)

# Difficulties
# Difficulties (distinct seeds + optional overrides)
DIFFICULTIES = {
    "Easy":   {"segments": 75,  "seed": 32, "min_passable_ratio": 0.75, "multi_wall_pct": 0.3, "layers": (1,1)},
    "Medium": {"segments": 120, "seed":32, "min_passable_ratio": 0.65, "multi_wall_pct": 0.4, "layers": (1,2)},
    "Hard":   {"segments": 180, "seed": 32, "min_passable_ratio": 0.55, "multi_wall_pct": 0.6, "layers": (1,2)},
}
# Fonts
DEFAULT_FONT = "Arial"


def make_window():
    return pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")