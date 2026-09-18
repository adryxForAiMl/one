from direct.showbase.ShowBase import ShowBase

from .flight_controller import FlightController


class KeyboardController:

    def __init__(self, base: ShowBase, controller: FlightController):
        self.base = base
        self.controller = controller

        self.keys = {
            "arrow_up": False,
            "arrow_down": False,
            "arrow_left": False,
            "arrow_right": False,
            "r": False,
            "f": False,
            "q": False,
            "e": False,
        }

        self._register_events()

    def _register_events(self):
        for key in self.keys:
            self.base.accept(
                key,
                self._set_key,
                [key, True]
            )

            self.base.accept(
                f"{key}-up",
                self._set_key,
                [key, False]
            )

    def _set_key(self, key, value):
        self.keys[key] = value

    def update(self, dt):
        pitch = 0.0
        roll = 0.0
        yaw = 0.0
        throttle_direction = 0.0

        if self.keys["arrow_up"]:
            pitch += 1.0

        if self.keys["arrow_down"]:
            pitch -= 1.0

        if self.keys["arrow_left"]:
            roll -= 1.0

        if self.keys["arrow_right"]:
            roll += 1.0

        if self.keys["q"]:
            yaw -= 1.0

        if self.keys["e"]:
            yaw += 1.0

        if self.keys["r"]:
            throttle_direction += 1.0

        if self.keys["f"]:
            throttle_direction -= 1.0

        self.controller.set_command(
            pitch=pitch,
            roll=roll,
            yaw=yaw,
        )

        if throttle_direction != 0.0:
            self.controller.update_throttle(
                throttle_direction,
                dt
            )

    def reset(self):
        for key in self.keys:
            self.keys[key] = False