import socket, json, threading, pyglet
from dual_view import RescuerView
from game import Game

HOST = '10.227.97.67'  
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

    pilot_game = Game()

    pilot_game.window.set_visible(False)

    pilot_game.window.switch_to()
    pilot_game.window.context.set_current()

    
    rescuer = RescuerView(pilot_game)

  
    threading.Thread(target=receive_state, args=(rescuer, conn), daemon=True).start()

    pyglet.app.run()

if __name__ == "__main__":
    main()
