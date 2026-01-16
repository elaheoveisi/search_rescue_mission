from minigrid.manual_control import ManualControl


class User:
    def __init__(self, env):
        self.env = env
        self.controller = ManualControl(env)

    def handle_key(self, event):
        self.controller.key_handler(event)

    def get_frame(self):
        return self.env.render()

    def reset(self):
        self.controller.reset()
