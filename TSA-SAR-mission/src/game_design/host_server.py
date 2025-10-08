import socket
import json
import threading
import time
import pyglet
from game import Game
import update  # runs movement & time logic so state stays live

HOST = "0.0.0.0"
PORT = 5050


def handle_client(conn, game):
    """Continuously send the current game state to the connected client."""
    # Ensure the game logic updates continuously
    pyglet.clock.schedule_interval(lambda dt: update.tick(game, dt), 1 / 60.0)
    pyglet.clock.schedule_interval(lambda dt: update.second(game, dt), 1.0)

    while True:
        try:
            # Serialize tuples/sets safely for JSON
            victims_serialized = {f"{x},{y}": v for (x, y), v in game.victims.items()}
            walls_serialized = [list(w) for w in game.walls]
            rescue_serialized = [list(r) for r in getattr(game, "rescue_positions", [])]

            state = {
                "player": list(game.player),
                "victims": victims_serialized,
                "walls": walls_serialized,
                "rescue_positions": rescue_serialized,
                "carried": game.carried,
                "time": game.time_remaining,
            }

            msg = json.dumps(state).encode() + b"\n"
            conn.sendall(msg)
            time.sleep(0.05)  # faster refresh for smoother sync

        except (BrokenPipeError, ConnectionResetError):
            print("[SERVER] Client disconnected.")
            break
        except Exception as e:
            print(f"[SERVER] Error sending state: {e}")
            break


def main():
    """Start the host game and wait for a rescuer client to connect."""
    game = Game()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[SERVER] Waiting for rescuer on {HOST}:{PORT}...")

    conn, addr = server.accept()
    print(f"[SERVER] Connected from {addr}")

    threading.Thread(target=handle_client, args=(conn, game), daemon=True).start()
    pyglet.app.run()


if __name__ == "__main__":
    main()
