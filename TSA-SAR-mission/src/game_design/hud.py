# hud.py
from collections import deque

import pyglet
from pyglet import shapes, text
from pyglet.window import key

from config import (
    PLAY_W_PX,
    SIDEBAR_W,
    WINDOW_HEIGHT,
    COLOR_PANEL_RGB,
    COLOR_PANEL_ALPHA,
    COLOR_PANEL_BORDER,
    COLOR_TEXT,
    DEFAULT_FONT,
)


def build_hud(ui_batch):
    """Build the right-side HUD panel and labels."""
    # Background panel on the right
    panel = shapes.BorderedRectangle(
        PLAY_W_PX,
        0,
        SIDEBAR_W,
        WINDOW_HEIGHT,
        border=2,
        color=COLOR_PANEL_RGB,
        border_color=COLOR_PANEL_BORDER,
        batch=ui_batch,
    )
    panel.opacity = COLOR_PANEL_ALPHA

    # Status line at top
    status = text.Label(
        "",
        x=PLAY_W_PX + SIDEBAR_W // 2,
        y=WINDOW_HEIGHT - 40,
        anchor_x="center",
        color=COLOR_TEXT,
        font_name=DEFAULT_FONT,
        font_size=14,
        batch=ui_batch,
    )

    # Labels dictionary
    labels = {
        "time": text.Label(
            "Time: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 80,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "zoom": text.Label(
            "Zoom: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 105,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "victims": text.Label(
            "Victims left: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 130,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "player": text.Label(
            "Player: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 155,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "carried": text.Label(
            "Carrying: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 205,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "difficulty": text.Label(
            "",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 230,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "view": text.Label(
            "View: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 255,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
    }

    return {"panel": panel, "status": status, "labels": labels}


# -----------------------------
# AI Q&A widgets for the HUD
# -----------------------------

# Quick question bank (edit/expand as you like)
# Quick question bank (final set)
MISSION_ADVISOR_QUESTIONS = [
    "what are the hazards and obstacles near me?",
    "where, how many and what are the nearest victim near me?",
    "where is the nearest rescue point?",
]

def default_hud_questions():
    """Returns the list shown as AI helper buttons."""
    return MISSION_ADVISOR_QUESTIONS


# HUDQuestions: clickable buttons + keys 1–5
BTN_W, BTN_H, BTN_PAD = 360, 32, 8


class HUDQuestions:
    def __init__(self, get_questions, on_send_question):
        self.get_questions = get_questions
        self.on_send_question = on_send_question
        self.batch = pyglet.graphics.Batch()
        self.labels = []
        self.buttons = []
        self.keys = [key._1, key._2, key._3, key._4, key._5]
        self.x, self.y = 20, 20  # default origin (call layout to reposition)

    def layout(self, x: int, y: int):
        self.x, self.y = x, y
        self._rebuild()

    def _rebuild(self):
        self.batch = pyglet.graphics.Batch()
        self.labels.clear()
        self.buttons.clear()
        qs = self.get_questions()
        for i, q in enumerate(qs):
            by = self.y - i * (BTN_H + BTN_PAD)
            rect = pyglet.shapes.Rectangle(
                self.x,
                by,
                BTN_W,
                BTN_H,
                batch=self.batch,
            )
            rect.opacity = 80
            lbl = pyglet.text.Label(
                f"{i + 1}. {q[:70]}{'…' if len(q) > 70 else ''}",
                x=self.x + 8,
                y=by + BTN_H // 2,
                anchor_y="center",
                color=(255, 255, 255, 255),
                batch=self.batch,
            )
            self.buttons.append(rect)
            self.labels.append(lbl)

    def draw(self):
        self.batch.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        qs = self.get_questions()
        for i, rect in enumerate(self.buttons):
            if rect.x <= x <= rect.x + rect.width and rect.y <= y <= rect.y + rect.height:
                self.on_send_question(qs[i])
                return True
        return False

    def on_key_press(self, symbol, modifiers):
        qs = self.get_questions()
        for i, k in enumerate(self.keys):
            if symbol == k and i < len(qs):
                self.on_send_question(qs[i])
                return True
        return False


# Simple scrolling chat log for AI replies
class ChatPanel:
    def __init__(self, width=480, height=180, max_lines=200):
        self.width = width
        self.height = height
        self.lines = deque(maxlen=max_lines)

    def post(self, who: str, text_str: str):
        prefix = "[YOU]" if who == "user" else "[AI]"
        for line in text_str.splitlines():
            self.lines.append(f"{prefix} {line}")

    def draw(self, x, y):
        y_cursor = y
        for line in list(self.lines)[-10:][::-1]:
            label = pyglet.text.Label(line, x=x, y=y_cursor, color=(230, 230, 230, 255))
            label.draw()
            y_cursor += 16