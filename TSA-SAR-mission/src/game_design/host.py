# client.py
import socket, threading, json, pyglet, argparse, os
from pyglet import shapes

CELL_SIZE = 20
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800

class ClientWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Client View")
        self.player = [0, 0]
        self.victims = {}
        self.carried = []
        self.batch = pyglet.graphics.Batch()

    def update_from_state(self, state):
        self.player = state["player"]
        self.victims = dict(state["victims"])
        self.carried = state["carried"]

    def on_draw(self):
        self.clear()
        self.batch = pyglet.graphics.Batch()
        for x in range(0, WINDOW_WIDTH, CELL_SIZE):
            shapes.Line(x, 0, x, WINDOW_HEIGHT, color=(70, 70, 70), batch=self.batch)
        for y in range(0, WINDOW_HEIGHT, CELL_SIZE):
            shapes.Line(0, y, WINDOW_WIDTH, y, color=(70, 70, 70), batch=self.batch)

        px, py = self.player
        shapes.Rectangle(px * CELL_SIZE, py * CELL_SIZE, CELL_SIZE, CELL_SIZE,
                         color=(60, 200, 255), batch=self.batch)

        for (vx, vy), kind in self.victims.items():
            color = (230, 70, 70) if kind == "red" else \
                    (190, 140, 255) if kind == "purple" else (255, 227, 102)
            shapes.Circle(vx * CELL_SIZE + CELL_SIZE//2,
                          vy * CELL_SIZE + CELL_SIZE//2,
                          CELL_SIZE//2 - 3, color=color, batch=self.batch)
        self.batch.draw()

def listen_thread(win: ClientWindow, server_host, server_port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {server_host}:{server_port} ...")
    s.connect((server_host, server_port))
    buffer = ""
    while True:
        data = s.recv(4096).decode()
        if not data:
            continue
        buffer += data
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if line.strip():
                state = json.loads(line)
                pyglet.clock.schedule_once(lambda dt: win.update_from_state(state), 0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("SAR_HOST", "127.0.0.1"),
                        help="Server host/IP to connect to")
    parser.add_argument("--port", type=int, default=int(os.getenv("SAR_PORT", "8765")),
                        help="Server port to connect to")
    args = parser.parse_args()

    window = ClientWindow()
    threading.Thread(target=listen_thread, args=(window, args.host, args.port), daemon=True).start()
    pyglet.app.run()

if __name__ == "__main__":
    main()
