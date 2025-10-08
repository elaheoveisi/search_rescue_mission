import socket
import json
import threading
import pyglet
from dual_view import RescuerView
from config import PLAY_W, PLAY_H

# ------------------------------
# Network configuration
# ------------------------------
HOST = "10.227.97.67"  # Replace with your Host machine's IP
PORT = 5050


# ------------------------------
# Lightweight mirror of Game() for the client
# ------------------------------
class MirrorGame:
    """
    A minimal game-like object for the rescuer client.
    It holds world state sent by the host without generating its own map.
    """
    def __init__(self):
        self.PLAY_W, self.PLAY_H = PLAY_W, PLAY_H
        self.walls = set()
        self.victims = {}
        self.rescue_positions = []
        self.carried = []
        self.time_remaining = 0
        self.player = (0, 0)
        self.state = "playing"
        self.view_mode = "global"
        self.zoom = 1.0
        self.difficulty = "—"
        self.game_over = False


# ------------------------------
# Network receive logic
# ------------------------------
def receive_state(rescuer, conn):
    """
    Receive game state updates from the host and update the local mirror game object.
    """
    buffer = ""
    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                break
            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue

                # Parse the JSON message
                state = json.loads(line)
                p = rescuer.pilot  # This is the MirrorGame instance

                # Update all relevant fields
                p.player = tuple(state.get("player", (0, 0)))
                p.victims = {
                    tuple(map(int, k.split(","))): v
                    for k, v in state.get("victims", {}).items()
                }
                p.walls = {tuple(w) for w in state.get("walls", [])}
                p.rescue_positions = [tuple(r) for r in state.get("rescue_positions", [])]
                p.carried = state.get("carried", [])
                p.time_remaining = state.get("time", 0)

                # Debug log (optional)
                # print(f"[CLIENT] State: {len(p.walls)} walls, {len(p.victims)} victims, player={p.player}")

                # Force redraw so HUD + map update immediately
                pyglet.clock.schedule_once(
                    lambda dt: rescuer.window.dispatch_event("on_draw"), 0
                )

        except Exception as e:
            print(f"[CLIENT] Error receiving state: {e}")
            break


# ------------------------------
# OpenGL context protection
# ------------------------------
def patch_opengl_context(rescuer):
    """
    Ensure correct OpenGL context before drawing (prevents invalid state errors).
    """
    original_draw = rescuer.on_draw

    def safe_draw():
        try:
            rescuer.window.switch_to()
            rescuer.window.context.set_current()
            original_draw()
        except Exception as e:
            print(f"[CLIENT] OpenGL context recovered: {e}")

    rescuer.on_draw = safe_draw


# ------------------------------
# Main client entry
# ------------------------------
def main():
    # Connect to the host
    conn = socket.create_connection((HOST, PORT))
    print(f"[CLIENT] Connected to {HOST}:{PORT}")

    # Use a minimal mirror of the game (no world generation)
    pilot_game = MirrorGame()

    # Create the rescuer HUD / visualizer window
    rescuer = RescuerView(pilot_game)

    # Prevent OpenGL context conflicts
    patch_opengl_context(rescuer)

    # Start a background thread to continuously receive host updates
    threading.Thread(target=receive_state, args=(rescuer, conn), daemon=True).start()

    pyglet.app.run()


if __name__ == "__main__":
    main()
