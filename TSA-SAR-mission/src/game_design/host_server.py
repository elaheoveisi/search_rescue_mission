import socket, json, threading, time
from game import Game

HOST = '0.0.0.0'
PORT = 5050

def handle_client(conn, game):
    while True:
        # send current game state every 0.1s
        state = {
            "player": game.player,
            "victims": game.victims,
            "walls": list(game.walls),
            "rescue_positions": list(game.rescue_positions),
            "carried": game.carried,
            "time": game.time_remaining
        }
        msg = json.dumps(state).encode()
        try:
            conn.sendall(msg + b'\n')
        except:
            break
        time.sleep(0.1)

def main():
    game = Game()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"[SERVER] Waiting for rescuer on {HOST}:{PORT}...")
    conn, addr = server.accept()
    print(f"[SERVER] Connected from {addr}")

    threading.Thread(target=handle_client, args=(conn, game), daemon=True).start()

    # normal pyglet run
    import pyglet
    pyglet.app.run()

if __name__ == "__main__":
    main()
