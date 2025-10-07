import socket, json, threading
from dual_view import RescuerView
from game import Game
import pyglet

HOST = '192.168.1.100'  # <-- replace with HOST computer’s IP
PORT = 5050

def receive_state(rescuer, conn):
    buffer = ""
    while True:
        data = conn.recv(4096).decode()
        if not data:
            break
        buffer += data
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            state = json.loads(line)
            # sync rescuer view with pilot state
            p = rescuer.pilot
            p.player = state["player"]
            p.victims = state["victims"]
            p.walls = set(map(tuple, state["walls"]))
            p.rescue_positions = state["rescue_positions"]
            p.carried = state["carried"]
            p.time_remaining = state["time"]

def main():
    conn = socket.create_connection((HOST, PORT))
    print(f"[CLIENT] Connected to {HOST}:{PORT}")

    pilot_stub = Game()  # a dummy game used for rendering only
    rescuer = RescuerView(pilot_stub)

    threading.Thread(target=receive_state, args=(rescuer, conn), daemon=True).start()
    pyglet.app.run()

if __name__ == "__main__":
    main()
