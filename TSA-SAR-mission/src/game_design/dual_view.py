# dual_view.py
import argparse
import pyglet
from pyglet import shapes

# --- your modules (must be in the same folder) ---
from game import Game                           # Pilot game (full logic)  :contentReference[oaicite:0]{index=0}
from config import PLAY_W, PLAY_H, COLOR_TEXT, CELL_SIZE, COLOR_WALL, COLOR_RESCUE  # sizes/colors :contentReference[oaicite:1]{index=1}
from world import victim_color                  # victim color helper       :contentReference[oaicite:2]{index=2}

# ------------------------------
# Rescuer (Global Overview) Window
# ------------------------------
class RescuerWindow(pyglet.window.Window):
    def __init__(self, game: Game, screen=None, fullscreen=False, pos=None, size=None):
        # Default size that scales the whole grid nicely
        if size is None:
            w = max(PLAY_W * 12, 800)
            h = max(PLAY_H * 12, 600)
        else:
            w, h = size

        super().__init__(width=int(w), height=int(h),
                         caption="SAR Rescuer (Global View)",
                         resizable=False, screen=screen)

        if (not fullscreen) and pos:
            try: self.set_location(int(pos[0]), int(pos[1]))
            except Exception: pass

        if fullscreen:
            self.set_fullscreen(True, screen=screen)

        self.game = game
        self.batch = pyglet.graphics.Batch()

    # ---------- helpers ----------
    def _cell_px(self):
        # scale each grid cell to fit the window
        cw = max(2, self.width // max(1, PLAY_W))
        ch = max(2, self.height // max(1, PLAY_H))
        return cw, ch

    def _to_px(self, gx, gy, cw, ch):
        return gx * cw, gy * ch

    def _draw_grid(self, cw, ch):
        for gx in range(1, PLAY_W):
            x = gx * cw
            shapes.Line(x, 0, x, self.height, color=(70, 70, 70), batch=self.batch)
        for gy in range(1, PLAY_H):
            y = gy * ch
            shapes.Line(0, y, self.width, y, color=(70, 70, 70), batch=self.batch)

    def _draw_walls(self, cw, ch):
        # We don't know which walls were colored orange in draw_world(), but we can render the structure.
        if getattr(self.game, "walls", None):
            for (wx, wy) in self.game.walls:
                x, y = self._to_px(wx, wy, cw, ch)
                shapes.Rectangle(x, y, cw, ch, color=COLOR_WALL, batch=self.batch)

    def _draw_victims(self, cw, ch):
        if getattr(self.game, "victims", None):
            r = max(2, int(min(cw, ch) / 2) - 2)
            for (vx, vy), kind in self.game.victims.items():
                cx = vx * cw + cw // 2
                cy = vy * ch + ch // 2
                shapes.Circle(cx, cy, r, color=victim_color(kind), batch=self.batch)

    def _draw_player(self, cw, ch):
        if getattr(self.game, "player", None):
            px, py = self.game.player
            x, y = self._to_px(px, py, cw, ch)
            shapes.Rectangle(x, y, cw, ch, color=(60, 200, 255), batch=self.batch)

            # carried indicators next to the player (max 3)
            carried = getattr(self.game, "carried", [])
            offs = [(-5, 6), (5, 6), (0, -6)]
            for i, k in enumerate(carried[:3]):
                cx = x + cw // 2 + offs[i][0]
                cy = y + ch // 2 + offs[i][1]
                shapes.Circle(cx, cy, max(2, int(min(cw, ch) * 0.12)),
                              color=victim_color(k), batch=self.batch)

    def _draw_rescue_triangles(self, cw, ch):
        # Game provides multiple rescue positions as a list (see game.rebuild_world()):contentReference[oaicite:3]{index=3}
        rps = getattr(self.game, "rescue_positions", []) or []
        for (gx, gy) in rps:
            # draw a triangle centered in the cell
            cx = gx * cw + cw / 2
            cy = gy * ch + ch / 2
            s = min(cw, ch) * 0.9
            h = s * 0.5
            shapes.Triangle(cx, cy + h, cx - s/2, cy - h, cx + s/2, cy - h,
                            color=COLOR_RESCUE, batch=self.batch)

    def _draw_status_text(self):
        # Time remaining & victim counts (read from the Pilot game state):contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}
        time_left = getattr(self.game, "time_remaining", 0)
        vs = getattr(self.game, "victims", {})
        reds = sum(1 for k in vs.values() if k == "red")
        purp = sum(1 for k in vs.values() if k == "purple")
        yell = sum(1 for k in vs.values() if k == "yellow")

        status = f"Time: {max(0, int(time_left))}s   Victims left (R/P/Y): {reds}/{purp}/{yell}"
        pyglet.text.Label(
            status, x=10, y=self.height - 10,
            anchor_x='left', anchor_y='top',
            color=COLOR_TEXT, font_name="Arial", font_size=12,
            batch=self.batch
        )

    # ---------- draw ----------
    def on_draw(self):
        self.clear()
        self.batch = pyglet.graphics.Batch()

        cw, ch = self._cell_px()
        self._draw_grid(cw, ch)
        self._draw_walls(cw, ch)             # NEW: walls
        self._draw_victims(cw, ch)
        self._draw_player(cw, ch)
        self._draw_rescue_triangles(cw, ch)  # NEW: rescue triangles
        self._draw_status_text()             # NEW: time & counts

        self.batch.draw()


def pick_screen(index: int | None):
    """Return pyglet screen by index (or None if invalid)."""
    if index is None:
        return None
    try:
        display = pyglet.canvas.get_display()
        screens = display.get_screens()
        if 0 <= index < len(screens):
            return screens[index]
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Run SAR Pilot (interactive) + Rescuer (global) on one PC with two monitors."
    )
    parser.add_argument("--pilot-screen", type=int, default=None,
                        help="Monitor index for the Pilot (0-based).")
    parser.add_argument("--rescuer-screen", type=int, default=None,
                        help="Monitor index for the Rescuer (0-based).")
    parser.add_argument("--pilot-fullscreen", action="store_true",
                        help="Pilot fullscreen on its monitor.")
    parser.add_argument("--rescuer-fullscreen", action="store_true",
                        help="Rescuer fullscreen on its monitor.")
    parser.add_argument("--pilot-x", type=int, help="Pilot window X.")
    parser.add_argument("--pilot-y", type=int, help="Pilot window Y.")
    parser.add_argument("--rescuer-x", type=int, help="Rescuer window X.")
    parser.add_argument("--rescuer-y", type=int, help="Rescuer window Y.")
    parser.add_argument("--rescuer-w", type=int, help="Rescuer window width.")
    parser.add_argument("--rescuer-h", type=int, help="Rescuer window height.")
    parser.add_argument("--pilot-default-local", action="store_true",
                        help="Force Pilot to start in Local camera mode.")

    args = parser.parse_args()

    # 1) Pilot (interactive, full game)
    game = Game()  # uses your existing logic, HUD, controls, timers, etc. :contentReference[oaicite:6]{index=6}

    pilot_screen = pick_screen(args.pilot_screen)
    if args.pilot_fullscreen:
        game.window.set_fullscreen(True, screen=pilot_screen)
    else:
        if args.pilot_x is not None and args.pilot_y is not None:
            try: game.window.set_location(int(args.pilot_x), int(args.pilot_y))
            except Exception: pass
        elif pilot_screen is not None:
            try: game.window.set_location(pilot_screen.x + 50, pilot_screen.y + 50)
            except Exception: pass

    # Optionally force Pilot to Local camera before starting (you also have Start screen toggles):contentReference[oaicite:7]{index=7}:contentReference[oaicite:8]{index=8}
    if args.pilot_default_local and hasattr(game, "view_mode"):
        game.view_mode = "local"
        if "labels" in game.hud and "view" in game.hud["labels"]:
            game.hud["labels"]["view"].text = f"View: {game.view_mode.capitalize()}"

    # 2) Rescuer (global, read-only, mirrors the Pilot's state)
    rescuer_screen = pick_screen(args.rescuer_screen)
    rescuer_size = (args.rescuer_w, args.rescuer_h) if args.rescuer_w and args.rescuer_h else None
    rescuer_pos = (args.rescuer_x, args.rescuer_y) if args.rescuer_x is not None and args.rescuer_y is not None else None

    rescuer = RescuerWindow(
        game=game,
        screen=rescuer_screen,
        fullscreen=args.rescuer_fullscreen,
        pos=rescuer_pos,
        size=rescuer_size
    )

    pyglet.app.run()


if __name__ == "__main__":
    main()
