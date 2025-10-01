# dual_view.py
import pyglet
from pyglet import shapes, text
from pyglet.window import key
from pyglet import canvas

# ---- Reuse your existing modules / constants ----
from config import (
    PLAY_W, PLAY_H, CELL_SIZE,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    COLOR_WALL, COLOR_RESCUE, COLOR_TEXT, COLOR_PLAYER,
    TIME_LIMIT, START
)
from camera import set_play_projection, reset_ui_projection
from grid import build_grid_lines
from hud import build_hud
from chatui import build_chat          # controls.py expects game.chat
from helpers import bfs_distances
from world import generate_walls, place_victims, draw_world, make_rescue_triangle, victim_color
from update import tick, second
from controls import key_press as pilot_key_press, mouse_press as pilot_mouse_press

# Keep strong refs so windows aren’t GC’d
_windows = []

# =========================================================
#                    PILOT (LOCAL VIEW)
# =========================================================
class GamePilot:
    """Owns the game state; interactive local view."""
    def __init__(self, screen, fullscreen=True, x=None, y=None, w=None, h=None):
        if fullscreen:
            self.window = pyglet.window.Window(fullscreen=True, screen=screen, caption="Pilot (Local)")
        else:
            ww = w if w is not None else WINDOW_WIDTH
            hh = h if h is not None else WINDOW_HEIGHT
            self.window = pyglet.window.Window(ww, hh, caption="Pilot (Local)")
            if x is not None and y is not None:
                self.window.set_location(x, y)
        self.window.push_handlers(self)

        # World/state
        self.PLAY_W, self.PLAY_H = PLAY_W, PLAY_H
        self.walls, self.orange_walls = set(), set()
        self.victims = {}
        self.passable = set()

        # Batches
        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        # Game vars
        self.state, self.zoom, self.view_mode = "start", 1.0, "local"
        self.time_remaining, self.game_over = TIME_LIMIT, False
        self.player = [*START]
        self.rescue_positions, self.rescue_shapes = [], []
        self.carried, self.carried_shapes = [], []

        # Drawn shapes
        self.grid_lines = build_grid_lines(self.play_batch)
        self.wall_shapes, self.victim_shapes = [], {}   # persistent world shapes
        self._overlay_shapes = []                       # transient local overlay (rebuilt per frame)

        # Player sprite (persistent, world coords)
        self.player_shape = shapes.Rectangle(0, 0, CELL_SIZE, CELL_SIZE, color=COLOR_PLAYER, batch=self.play_batch)

        # HUD + CHAT (controls.py expects chat dict with focus/caret)
        self.hud = build_hud(self.ui_batch)
        self.hud["status"].text = "Press ENTER on Start screen to begin"
        self.chat = build_chat(self.ui_batch)

        # Start screen UI
        self.start_diffs = ["Easy", "Medium", "Hard"]
        self.start_diff_idx = 0
        self.start_view = "Local"
        cx, cy = self.window.width // 2, self.window.height // 2
        self.start_title = text.Label("Mission Setup", x=cx, y=cy + 80, anchor_x="center", color=COLOR_TEXT, font_size=28)
        self.start_diff_label = text.Label("", x=cx, y=cy + 30, anchor_x="center", color=COLOR_TEXT, font_size=18)
        self.start_view_label = text.Label("", x=cx, y=cy - 10, anchor_x="center", color=COLOR_TEXT, font_size=18)
        self.start_hint = text.Label("Use 1-2-3 • ENTER to start", x=cx, y=cy - 60, anchor_x="center", color=COLOR_TEXT, font_size=12)
        self.refresh_start_labels()

        # Tickers
        pyglet.clock.schedule_interval(lambda dt: tick(self, dt), 1 / 60.0)
        pyglet.clock.schedule_interval(lambda dt: second(self, dt), 1.0)

    # ---------- world building ----------
    def rebuild_world(self):
        for shape_list in [self.wall_shapes, self.rescue_shapes, self.carried_shapes]:
            for s in shape_list:
                s.delete()
        for c, _ in self.victim_shapes.values():
            c.delete()
        self.wall_shapes.clear()
        self.victim_shapes.clear()
        self.rescue_shapes.clear()
        self.carried_shapes.clear()
        self.carried = []

        self.walls, self.orange_walls = generate_walls(self.difficulty)
        self.passable = {(x, y) for x in range(PLAY_W) for y in range(PLAY_H)} - self.walls
        distmap = bfs_distances(START, self.passable)
        self.victims = place_victims(distmap, START, self.passable)

        import random
        pool = list(self.passable - set(self.victims.keys()) - {START})
        self.rescue_positions = random.sample(pool, min(3, len(pool)))

        self.wall_shapes, self.victim_shapes = draw_world(self.play_batch, self.walls, self.orange_walls, self.victims)
        for rp in self.rescue_positions:
            tri = make_rescue_triangle(self.play_batch, rp)
            if tri:
                self.rescue_shapes.append(tri)

        self.player[:] = START
        self.time_remaining = TIME_LIMIT

    # ---------- start helpers ----------
    def refresh_start_labels(self):
        d = self.start_diffs[self.start_diff_idx]
        self.start_diff_label.text = f"Difficulty:  {d}"
        self.start_view_label.text = f"View:        {self.start_view}"

    def apply_start_and_begin(self):
        self.difficulty = self.start_diffs[self.start_diff_idx]
        self.view_mode = "local"
        self.rebuild_world()
        self.state = "playing"
        self.hud["status"].text = ""

    # ---------- carrying ----------
    def add_carried(self, kind):
        if len(self.carried) < 3:
            self.carried.append(kind)
            self._sync_carried_sprites()

    def drop_all_carried(self):
        self.carried.clear()
        self._sync_carried_sprites()

    def _sync_carried_sprites(self):
        while len(self.carried_shapes) > len(self.carried):
            self.carried_shapes.pop().delete()
        while len(self.carried_shapes) < len(self.carried):
            self.carried_shapes.append(shapes.Circle(0, 0, CELL_SIZE * 0.22, batch=self.play_batch))
        self.update_carried_position()
        for i, kind in enumerate(self.carried):
            self.carried_shapes[i].color = victim_color(kind)

    def update_carried_position(self):
        offs = [(-5, 6), (5, 6), (0, -6)]
        for i, s in enumerate(self.carried_shapes):
            s.x = self.player[0] * CELL_SIZE + CELL_SIZE / 2 + offs[i][0]
            s.y = self.player[1] * CELL_SIZE + CELL_SIZE / 2 + offs[i][1]

    # ---------- local overlay (player-centered) ----------
    def _local_cell_px(self):
        return CELL_SIZE, CELL_SIZE

    def _local_to_px(self, gx, gy, cw, ch):
        px, py = self.player
        off_x = self.window.width // 2 - px * cw
        off_y = self.window.height // 2 - py * ch
        return gx * cw + off_x, gy * ch + off_y

    def _local_draw_walls(self, cw, ch, R=5):
        px, py = self.player
        for (wx, wy) in self.walls:
            if abs(wx - px) > R or abs(wy - py) > R:
                continue
            x, y = self._local_to_px(wx, wy, cw, ch)
            self._overlay_shapes.append(shapes.Rectangle(x, y, cw, ch, color=COLOR_WALL, batch=self.play_batch))

    def _local_draw_victims(self, cw, ch, R=5):
        if not self.victims:
            return
        r = max(2, int(min(cw, ch) / 2) - 2)
        px, py = self.player
        for (vx, vy), kind in self.victims.items():
            if abs(vx - px) > R or abs(vy - py) > R:
                continue
            cx, cy = self._local_to_px(vx, vy, cw, ch)
            cx += cw // 2
            cy += ch // 2
            self._overlay_shapes.append(shapes.Circle(cx, cy, r, color=victim_color(kind), batch=self.play_batch))

    def _local_draw_rescues(self, cw, ch, R=5):
        for (gx, gy) in self.rescue_positions:
            px, py = self.player
            if abs(gx - px) > R or abs(gy - py) > R:
                continue
            cx, cy = self._local_to_px(gx, gy, cw, ch)
            s = min(cw, ch) * 0.9
            h = s * 0.5
            self._overlay_shapes.append(
                shapes.Triangle(cx, cy + h, cx - s / 2, cy - h, cx + s / 2, cy - h, color=COLOR_RESCUE, batch=self.play_batch)
            )

    def _local_draw_player(self, cw, ch):
        x = self.window.width // 2
        y = self.window.height // 2
        self._overlay_shapes.append(shapes.Rectangle(x - cw // 2, y - ch // 2, cw, ch, color=(60, 200, 255), batch=self.play_batch))
        offs = [(-5, 6), (5, 6), (0, -6)]
        for i, k in enumerate(self.carried[:3]):
            cx, cy = x + offs[i][0], y + offs[i][1]
            self._overlay_shapes.append(shapes.Circle(cx, cy, max(2, int(min(cw, ch) * 0.12)), color=victim_color(k), batch=self.play_batch))

    def _build_local_overlay(self):
        cw, ch = self._local_cell_px()
        self._local_draw_walls(cw, ch)
        self._local_draw_victims(cw, ch)
        self._local_draw_rescues(cw, ch)
        self._local_draw_player(cw, ch)

    # ---------- drawing ----------
    def on_draw(self):
        self.window.switch_to()  # ensure this window's GL context is current

        # clear last frame overlay
        for s in self._overlay_shapes:
            try:
                s.delete()
            except:
                pass
        self._overlay_shapes.clear()

        self.window.clear()
        set_play_projection(self.window, self.player, self.view_mode, self.zoom)

        if self.state == "playing":
            self._build_local_overlay()

        self.play_batch.draw()
        reset_ui_projection(self.window)
        self.ui_batch.draw()

        if self.state == "start":
            self.start_title.draw()
            self.start_diff_label.draw()
            self.start_view_label.draw()
            self.start_hint.draw()

    # ---------- input (pilot only) ----------
    def on_key_press(self, symbol, modifiers):
        if self.state == "start":
            if symbol == key.ENTER:
                self.apply_start_and_begin()
                return
            if symbol in (key._1, key.NUM_1):
                self.start_diff_idx = 0
                self.refresh_start_labels()
                return
            if symbol in (key._2, key.NUM_2):
                self.start_diff_idx = 1
                self.refresh_start_labels()
                return
            if symbol in (key._3, key.NUM_3):
                self.start_diff_idx = 2
                self.refresh_start_labels()
                return
            return
        pilot_key_press(self, symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        pilot_mouse_press(self, x, y, button, modifiers)

    # --- caret passthrough for chat entry (controls.py expects this) ---
    def on_text(self, s):
        if self.chat["focus"] and self.chat["caret"]:
            self.chat["caret"].on_text(s)

    def on_text_motion(self, m):
        if self.chat["focus"] and self.chat["caret"]:
            self.chat["caret"].on_text_motion(m)


# =========================================================
#                 RESCUER (GLOBAL VIEW)
# =========================================================
class RescuerView:
    """Read-only global map that mirrors the pilot state."""
    def __init__(self, pilot: GamePilot, screen, fullscreen=True, x=None, y=None, w=None, h=None):
        self.pilot = pilot
        if fullscreen:
            self.window = pyglet.window.Window(fullscreen=True, screen=screen, caption="Rescuer (Global)")
        else:
            ww = w if w is not None else WINDOW_WIDTH
            hh = h if h is not None else WINDOW_HEIGHT
            self.window = pyglet.window.Window(ww, hh, caption="Rescuer (Global)")
            if x is not None and y is not None:
                self.window.set_location(x, y)
        self.window.push_handlers(self)

        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()
        self._frame_shapes = []

        # A little status label (shows "waiting" if pilot hasn't started yet)
        self.title = text.Label("Rescuer Global View (read-only)",
                                x=20, y=self.window.height - 28,
                                color=(210, 210, 255, 255), font_size=12)
        self.waiting = text.Label("Waiting for Pilot to start (press ENTER in Pilot window)",
                                  x=20, y=self.window.height - 52,
                                  color=(210, 210, 210, 255), font_size=10)

    def _clear_frame(self):
        for s in self._frame_shapes:
            try:
                s.delete()
            except:
                pass
        self._frame_shapes.clear()

    def _draw_global(self):
        cw = CELL_SIZE
        ch = CELL_SIZE

        # Walls
        for (wx, wy) in self.pilot.walls:
            self._frame_shapes.append(shapes.Rectangle(wx * cw, wy * ch, cw, ch, color=COLOR_WALL, batch=self.play_batch))

        # Victims
        r = max(2, int(min(cw, ch) / 2) - 2)
        for (vx, vy), kind in self.pilot.victims.items():
            cx = vx * cw + cw // 2
            cy = vy * ch + ch // 2
            self._frame_shapes.append(shapes.Circle(cx, cy, r, color=victim_color(kind), batch=self.play_batch))

        # Rescue points
        for (gx, gy) in self.pilot.rescue_positions:
            cx = gx * cw
            cy = gy * ch
            s = min(cw, ch) * 0.9
            h = s * 0.5
            self._frame_shapes.append(
                shapes.Triangle(cx, cy + h, cx - s / 2, cy - h, cx + s / 2, cy - h, color=COLOR_RESCUE, batch=self.play_batch)
            )

        # Player
        px, py = self.pilot.player
        self._frame_shapes.append(shapes.Rectangle(px * cw, py * ch, cw, ch, color=(60, 200, 255), batch=self.play_batch))

        # Carried markers
        offs = [(-5, 6), (5, 6), (0, -6)]
        cxp = px * cw + cw // 2
        cyp = py * ch + ch // 2
        for i, k in enumerate(self.pilot.carried[:3]):
            self._frame_shapes.append(
                shapes.Circle(cxp + offs[i][0], cyp + offs[i][1], max(2, int(min(cw, ch) * 0.12)), color=victim_color(k), batch=self.play_batch)
            )

    def on_draw(self):
        self.window.switch_to()  # ensure this window's GL context is current

        self._clear_frame()
        self.window.clear()

        # Use the "global" camera to scale the entire playfield to this window
        set_play_projection(self.window, self.pilot.player, "global", 1.0)

        # If the pilot hasn't started yet, show a helpful hint. Otherwise draw the map.
        if self.pilot.state != "playing":
            # Still draw title in UI projection
            reset_ui_projection(self.window)
            self.title.draw()
            self.waiting.draw()
        else:
            self._draw_global()
            self.play_batch.draw()
            reset_ui_projection(self.window)
            self.ui_batch.draw()
            self.title.draw()

    # read-only for now, BUT forward keyboard to Pilot so movement works even if this window is focused
    def on_key_press(self, symbol, modifiers):
        pilot_key_press(self.pilot, symbol, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        # No mouse controls for rescuer yet
        pass


# =========================================================
#                        ENTRYPOINT
# =========================================================
def main():
    disp = canvas.get_display()
    screens = disp.get_screens()

    if len(screens) >= 2:
        # Two monitors → fullscreen on each
        pilot = GamePilot(screen=screens[0], fullscreen=True)
        rescuer = RescuerView(pilot, screen=screens[1], fullscreen=True)
        _windows.extend([pilot, rescuer])
    else:
        screen = screens[0]
        sw, sh = screen.width, screen.height

        # Fit two windows across the width; keep at least 400px each
        half_w = max(400, sw // 2)
        win_h = min(max(400, WINDOW_HEIGHT), sh)

        # Left = Pilot, Right = Rescuer
        pilot = GamePilot(screen=screen, fullscreen=False, x=0, y=0, w=half_w, h=win_h)
        rescuer = RescuerView(pilot, screen=screen, fullscreen=False, x=half_w, y=0, w=half_w, h=win_h)
        _windows.extend([pilot, rescuer])

    pyglet.app.run()


if __name__ == "__main__":
    main()
