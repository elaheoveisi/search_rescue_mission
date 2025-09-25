# game.py
import random
import time
from typing import Optional

import pyglet
from pyglet import shapes, text
from pyglet.window import key

from config import *
from camera import set_play_projection, reset_ui_projection
from grid import build_grid_lines
from hud import build_hud, HUDQuestions, ChatPanel, default_hud_questions
from chatui import build_chat
from helpers import bfs_distances
from world import generate_walls, place_victims, draw_world, make_rescue_triangle, victim_color
from update import tick, second
from controls import key_press, mouse_press
from ai_backend import AIWorker, HFLocalLLM # Consolidated AI imports

# --------------------------------------------------------------------
# AI HELPER INTERFACE
# --------------------------------------------------------------------

MISSION_ADVISOR_SYSTEM_PROMPT = (
    "You are a SAR mission advisor. Your task is to analyze a map grid matrix, "
    "identify key features like wall structures (especially orange ones) and victim locations and rescue point, "
    "and provide a concise situational summary. You must describe the environment to improve the "
    "pilot's awareness. Do NOT give direct commands like 'go left' or 'move to X,Y'. "
    "Focus on descriptive guidance, like 'A dense cluster of victims is located in the southeast, "
    "partially enclosed by orange walls.' or 'The northern sector appears to be a maze of gray walls.'"
)
GENERAL_SYSTEM_PROMPT = (
    "You are an assistant for a UAS Search-and-Rescue (SAR) training game. "
    "Give concise, actionable answers. If asked about obstacles, warn that "
    "ATC does not track obstacles; pilots must visually avoid them. ")


# In game.py, replace the entire AIInterface class with this:
class AIInterface:
    """Handles the AI model, worker thread, and UI components."""
    def __init__(self, window, game):
        self.game = game
        self.chat_panel = ChatPanel(width=480, height=180)
        self.question_hud = HUDQuestions(
            get_questions=default_hud_questions,
            on_send_question=self._send_question
        )
        self.title = text.Label(
            "AI Helper (click or press 1–5)",
            x=20, y=WINDOW_HEIGHT - 24,
            color=(210, 210, 255, 255),
            font_size=12, bold=True
        )
        self.question_hud.layout(20, window.height - 52)
        self.model = HFLocalLLM()
        self.worker = AIWorker(self.model)

    def _on_ai_done(self, answer: str):
        """Callback function to handle the AI's response."""
        if not answer or not answer.strip():
            answer = "(The AI returned an empty or invalid response.)"
        self.chat_panel.post("ai", answer)

    def _send_question(self, question: str):
        if self.game.state != "playing":
            self.chat_panel.post(
                "ai",
                "Please start the mission first by pressing ENTER on the setup screen."
            )
            return

        self.chat_panel.post("user", question)

        # Always include matrix and player state
        matrix = self.game.get_matrix()
        matrix_str = "\n".join(["".join(map(str, row)) for row in matrix])
        player_pos = self.game.player
        rescue_points = getattr(self.game, "rescue_positions", [])

        prompt = f"""
You are assisting in a UAS Search-and-Rescue (SAR) mission.

My current position is {player_pos}.
Rescue points are at: {rescue_points if rescue_points else "unknown"}.

Map Legend:
- 9: My Position
- 1: Clear/Passable Terrain
- 0: Gray Wall (Obstacle)
- 5: Orange Wall (Obstacle, significant hazard)
- 2: Red Victim (High Priority)
- 3: Purple Victim (Medium Priority)
- 4: Yellow Victim (Low Priority)

Map Grid (top-down view):
{matrix_str}

Now answer this question clearly and concisely:
"{question}"
"""

        self.worker.ask(
            prompt,
            on_done=self._on_ai_done,
            system=MISSION_ADVISOR_SYSTEM_PROMPT
        )

    def draw(self, window):
        self.title.draw()
        self.question_hud.draw()
        self.chat_panel.draw(x=window.width - 500, y=40)

    def on_key_press(self, symbol, modifiers):
        return self.question_hud.on_key_press(symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        return self.question_hud.on_mouse_press(x, y, button, modifiers)

# --------------------------------------------------------------------
# GAME CLASS
# --------------------------------------------------------------------

class Game:
    def __init__(self):
        self.window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")
        self.window.push_handlers(self)

        # World attributes (initialized before use)
        self.PLAY_W, self.PLAY_H = PLAY_W, PLAY_H
        self.walls, self.orange_walls = set(), set()
        self.victims = {}
        self.passable = set()
        
        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        self.state, self.zoom, self.view_mode = "start", 1.0, "local"
        self.time_remaining, self.game_over = TIME_LIMIT, False
        self.player = [*START]
        self.rescue_positions, self.rescue_shapes = [], []
        self.carried, self.carried_shapes = [], []

        self.grid_lines = build_grid_lines(self.play_batch)
        self.wall_shapes, self.victim_shapes = [], {}

        self.player_shape = shapes.Rectangle(0, 0, CELL_SIZE, CELL_SIZE, color=COLOR_PLAYER, batch=self.play_batch)
        self.hud = build_hud(self.ui_batch)
        self.hud["status"].text = "Press ENTER on Start screen to begin"

        self.start_diffs = ["Easy", "Medium", "Hard"]
        self.start_diff_idx = 0
        self.start_view = "Local"
        self.start_title = text.Label("Mission Setup", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2+80, anchor_x="center", color=COLOR_TEXT, font_size=28, bold=True)
        self.start_diff_label = text.Label("", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2+30, anchor_x="center", color=COLOR_TEXT, font_size=18)
        self.start_view_label = text.Label("", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2-10, anchor_x="center", color=COLOR_TEXT, font_size=18)
        self.start_hint = text.Label("Use arrows / 1-2-3 / L-G • Press ENTER to start", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2-60, anchor_x="center", color=COLOR_TEXT, font_size=12)
        self.refresh_start_labels()

        self.chat = build_chat(self.ui_batch)
        pyglet.clock.schedule_interval(lambda dt: tick(self, dt), 1 / 60.0)
        pyglet.clock.schedule_interval(lambda dt: second(self, dt), 1.0)
        self.ai_interface = AIInterface(self.window, self)

    def get_matrix(self):
        matrix = [[1 for _ in range(self.PLAY_W)] for _ in range(self.PLAY_H)]
        for (x, y) in self.walls:
            matrix[y][x] = 5 if (x, y) in self.orange_walls else 0
        for (x, y), kind in self.victims.items():
            if kind == "red": matrix[y][x] = 2
            elif kind == "purple": matrix[y][x] = 3
            elif kind == "yellow": matrix[y][x] = 4
        px, py = self.player
        if 0 <= px < self.PLAY_W and 0 <= py < self.PLAY_H:
            matrix[py][px] = 9
        return matrix

    def refresh_start_labels(self):
        d = self.start_diffs[self.start_diff_idx]
        self.start_diff_label.text = f"Difficulty:  {d}"
        self.start_view_label.text = f"View:        {self.start_view}"

    def apply_start_and_begin(self):
        self.difficulty = self.start_diffs[self.start_diff_idx]
        self.view_mode = self.start_view.lower()
        self.rebuild_world()
        self.state = "playing"
        self.hud["status"].text = ""

    def rebuild_world(self):
        for shape_list in [self.wall_shapes, self.rescue_shapes, self.carried_shapes]:
            for s in shape_list: s.delete()
        for c, _ in self.victim_shapes.values(): c.delete()
        self.wall_shapes.clear(); self.victim_shapes.clear(); self.rescue_shapes.clear(); self.carried_shapes.clear()
        
        self.carried = []
        
        self.walls, self.orange_walls = generate_walls(self.difficulty)
        self.passable = {(x, y) for x in range(PLAY_W) for y in range(PLAY_H)} - self.walls
        distmap = bfs_distances(START, self.passable)
        self.victims = place_victims(distmap, START, self.passable)

        possible_rescue_points = list(self.passable - set(self.victims.keys()) - {START})
        self.rescue_positions = random.sample(possible_rescue_points, min(3, len(possible_rescue_points)))
        
        self.wall_shapes, self.victim_shapes = draw_world(self.play_batch, self.walls, self.orange_walls, self.victims)
        for rp in self.rescue_positions:
            self.rescue_shapes.append(make_rescue_triangle(self.play_batch, rp))
        
        self.player = [*START]
        self.time_remaining = TIME_LIMIT

    def add_carried(self, kind):
        if len(self.carried) < 3: self.carried.append(kind); self._sync_carried_sprites()

    def drop_all_carried(self):
        self.carried.clear(); self._sync_carried_sprites()

    def _sync_carried_sprites(self):
        while len(self.carried_shapes) > len(self.carried): self.carried_shapes.pop().delete()
        while len(self.carried_shapes) < len(self.carried): self.carried_shapes.append(shapes.Circle(0, 0, CELL_SIZE * 0.22, batch=self.play_batch))
        self.update_carried_position()
        for i, kind in enumerate(self.carried): self.carried_shapes[i].color = victim_color(kind)

    def update_carried_position(self):
        offs = [(-5, 6), (5, 6), (0, -6)]
        for i, s in enumerate(self.carried_shapes):
            s.x = self.player[0] * CELL_SIZE + CELL_SIZE / 2 + offs[i][0]
            s.y = self.player[1] * CELL_SIZE + CELL_SIZE / 2 + offs[i][1]

    def on_draw(self):
        self.window.clear(); set_play_projection(self.window, self.player, self.view_mode, self.zoom)
        self.play_batch.draw(); reset_ui_projection(self.window); self.ui_batch.draw()
        if self.state == "start": self.start_title.draw(); self.start_diff_label.draw(); self.start_view_label.draw(); self.start_hint.draw()
        self.ai_interface.draw(self.window)

    def on_key_press(self, symbol, modifiers):
        if self.ai_interface.on_key_press(symbol, modifiers): return
        key_press(self, symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.ai_interface.on_mouse_press(x, y, button, modifiers): return
        mouse_press(self, x, y, button, modifiers)

    def on_text(self, s):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text(s)

    def on_text_motion(self, m):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text_motion(m)