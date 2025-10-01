import pyglet
from pyglet import shapes
from pyglet import canvas

from game import Game
from camera import reset_ui_projection
from world import victim_color
from hud import build_hud
from grid import build_grid_lines
from config import (
    CELL_SIZE, COLOR_WALL, COLOR_RESCUE, COLOR_PLAYER,
    WINDOW_WIDTH, WINDOW_HEIGHT, PLAY_W_PX, SIDEBAR_W
)

_windows = []


class RescuerView:
    """Global map that mirrors the pilot game, with full HUD and sidebar."""
    def __init__(self, pilot: Game, x=200, y=200, w=WINDOW_WIDTH, h=WINDOW_HEIGHT):
        self.pilot = pilot
        self.window = pyglet.window.Window(w, h, caption="Rescuer (Global)")
        self.window.set_location(x, y)
        self.window.push_handlers(self)

        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()
        self._frame_shapes = []
        self.grid_lines = []

        # HUD identical to Pilot
        self.hud = build_hud(self.ui_batch)

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
            self._frame_shapes.append(
                shapes.Rectangle(wx * cw, wy * ch, cw, ch, color=COLOR_WALL, batch=self.play_batch)
            )

        # Victims
        r = max(2, int(min(cw, ch) / 2) - 2)
        for (vx, vy), kind in self.pilot.victims.items():
            cx = vx * cw + cw // 2
            cy = vy * ch + ch // 2
            self._frame_shapes.append(
                shapes.Circle(cx, cy, r, color=victim_color(kind), batch=self.play_batch)
            )

        # Rescue points (fixed: centered like Pilot)
        for (gx, gy) in self.pilot.rescue_positions:
            cx = gx * cw + cw // 2
            cy = gy * ch + ch // 2
            s = cw * 0.9
            h = s * 0.5
            self._frame_shapes.append(
                shapes.Triangle(cx, cy + h, cx - s / 2, cy - h, cx + s / 2, cy - h,
                                color=COLOR_RESCUE, batch=self.play_batch)
            )

        # Player
        px, py = self.pilot.player
        self._frame_shapes.append(
            shapes.Rectangle(px * cw, py * ch, cw, ch, color=COLOR_PLAYER, batch=self.play_batch)
        )

    def on_draw(self):
        self.window.switch_to()

        if not self.grid_lines:
            self.grid_lines = build_grid_lines(self.play_batch)

        self._clear_frame()
        self.window.clear()

        # Projection for playfield only (leave room for sidebar HUD)
        world_w = PLAY_W_PX
        world_h = WINDOW_HEIGHT
        self.window.projection = pyglet.math.Mat4.orthogonal_projection(
            0, world_w, 0, world_h, -1.0, 1.0
        )

        if self.pilot.state == "playing":
            self._draw_global()
            self.play_batch.draw()

        # Reset projection for HUD (drawn in sidebar)
        reset_ui_projection(self.window)
        self.ui_batch.draw()

        # HUD mirrored from Pilot
        self.hud["labels"]["time"].text = f"Time: {self.pilot.time_remaining}"
        self.hud["labels"]["zoom"].text = f"Zoom: {self.pilot.zoom:.2f}"
        self.hud["labels"]["victims"].text = f"Victims left: {len(self.pilot.victims)}"
        self.hud["labels"]["player"].text = f"Player: {tuple(self.pilot.player)}"
        self.hud["labels"]["carried"].text = f"Carrying: {self.pilot.carried}"
        self.hud["labels"]["difficulty"].text = f"Difficulty: {getattr(self.pilot, 'difficulty', '—')}"
        self.hud["labels"]["view"].text = "View: Global"

    def on_key_press(self, symbol, modifiers):
        from controls import key_press as pilot_key_press
        pilot_key_press(self.pilot, symbol, modifiers)


def main():
    screen = canvas.get_display().get_screens()[0]

    # Pilot window
    pilot = Game()
    pilot.window.set_size(WINDOW_WIDTH, WINDOW_HEIGHT)
    pilot.window.set_location(50, 50)

    # Rescuer window
    rescuer = RescuerView(pilot, x=200, y=200, w=WINDOW_WIDTH, h=WINDOW_HEIGHT)

    _windows.extend([pilot, rescuer])
    pyglet.app.run()


if __name__ == "__main__":
    main()
