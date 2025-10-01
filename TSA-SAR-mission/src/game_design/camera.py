import pyglet
from pyglet import gl
from config import (
    PLAY_W_PX, WINDOW_HEIGHT, WINDOW_WIDTH,
    MIN_ZOOM, MAX_ZOOM, CELL_SIZE, PLAY_W, PLAY_H
)


def set_play_projection(window, player, view_mode, zoom):
    """
    Camera projection:
      - Global = full map, center-follow with zoom
      - Local  = starts as 5x5 zone (2 overlap). When zoom changes,
                 the edge triggers & stride depend on how many grid
                 cells are actually visible at the current zoom.

    Change requested:
      - When the player hits an edge/corner in LOCAL view, pan the camera
        by exactly ONE GRID CELL instead of jumping by a whole window.
    """
    gl.glViewport(0, 0, PLAY_W_PX, WINDOW_HEIGHT)

    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    z = max(MIN_ZOOM, min(MAX_ZOOM, zoom))

    # Player center in world pixels
    cx = (player[0] + 0.5) * CELL_SIZE
    cy = (player[1] + 0.5) * CELL_SIZE

    if view_mode == "global":
        # ----- Global: center-follow with zoom -----
        w = min(world_w, world_w / z)
        h = min(world_h, world_h / z)
        left   = max(0.0, min(cx - w / 2.0, world_w - w))
        bottom = max(0.0, min(cy - h / 2.0, world_h - h))

    else:
        # ----- Local: 5x5 start, then zoom-aware edges & stride -----
        BASE_ZONE_W_CELLS = 5
        BASE_ZONE_H_CELLS = 5
        OVERLAP_CELLS     = 2  # used when adjusting to zoom changes

        if not hasattr(window, "_cam_state"):
            window._cam_state = {}
        cam = window._cam_state

        # First time entering local: align around player using 5x5 zone
        if cam.get("mode") != "local":
            cam["mode"] = "local"
            base_zone_w = BASE_ZONE_W_CELLS * CELL_SIZE
            base_zone_h = BASE_ZONE_H_CELLS * CELL_SIZE
            left   = max(0, min(cx - base_zone_w // 2, world_w - base_zone_w))
            bottom = max(0, min(cy - base_zone_h // 2, world_h - base_zone_h))
            cam["left"], cam["bottom"] = left, bottom

        # --- Compute visible window (in world px) at current zoom,
        #     snapped to whole cells so edges line up with grid.
        base_zone_w = BASE_ZONE_W_CELLS * CELL_SIZE
        base_zone_h = BASE_ZONE_H_CELLS * CELL_SIZE
        vis_cells_x = max(1, int((base_zone_w / z) / CELL_SIZE))
        vis_cells_y = max(1, int((base_zone_h / z) / CELL_SIZE))
        w = vis_cells_x * CELL_SIZE
        h = vis_cells_y * CELL_SIZE

        # Stride used ONLY for fitting after zoom changes (not for edge panning)
        overlap_px = OVERLAP_CELLS * CELL_SIZE
        stride_x = max(CELL_SIZE, w - overlap_px)
        stride_y = max(CELL_SIZE, h - overlap_px)

        # Current camera rect origin
        left, bottom = cam["left"], cam["bottom"]

        # --- If zoom changed, ensure player is still inside the new visible rect.
        #     Step repeatedly by stride until inside (handles big zoom jumps).
        while cx < left and left > 0:
            left = max(0, left - stride_x)
        while cx >= left + w and left < world_w - w:
            left = min(world_w - w, left + stride_x)

        while cy < bottom and bottom > 0:
            bottom = max(0, bottom - stride_y)
        while cy >= bottom + h and bottom < world_h - h:
            bottom = min(world_h - h, bottom + stride_y)

        # --- One-cell pan when the player enters the edge cell(s)
        #EDGE_STEP = CELL_SIZE   # move exactly one grid cell
    # --- Always center the 5x5 (or 7x7) window on the player
    left = max(0, min(cx - w // 2, world_w - w))
    bottom = max(0, min(cy - h // 2, world_h - h))

    cam["left"], cam["bottom"] = left, bottom


    # Final projection using the zoom-aware visible window
    right = left + w
    top   = bottom + h

    window.projection = pyglet.math.Mat4.orthogonal_projection(
        left, right, bottom, top, -1.0, 1.0
    )

    # Keep the original return contract so nothing else breaks.
    return 2 if view_mode == "local" else 5


def reset_ui_projection(window):
    """Reset projection for HUD/UI drawing (screen-space coords)."""
    gl.glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        0.0, float(WINDOW_WIDTH), 0.0, float(WINDOW_HEIGHT), -1.0, 1.0
    )


def camera():
    """Factory to expose camera functions."""
    return {
        "set_play_projection": set_play_projection,
        "reset_ui_projection": reset_ui_projection
    }
