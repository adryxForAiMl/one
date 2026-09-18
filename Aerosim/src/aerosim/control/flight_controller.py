from dataclasses import dataclass
import numpy as np


@dataclass
class FlightCommand:
    throttle: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0


class FlightController:

    def __init__(self):
        self.command = FlightCommand()

        self.max_tilt = 0.30
        self.max_yaw = 0.20

        self.throttle_speed = 0.60

    def set_command(
        self,
        throttle=None,
        pitch=None,
        roll=None,
        yaw=None,
    ):
        if throttle is not None:
            self.command.throttle = float(
                np.clip(throttle, 0.0, 1.0)
            )

        if pitch is not None:
            self.command.pitch = float(
                np.clip(pitch, -1.0, 1.0)
            )

        if roll is not None:
            self.command.roll = float(
                np.clip(roll, -1.0, 1.0)
            )

        if yaw is not None:
            self.command.yaw = float(
                np.clip(yaw, -1.0, 1.0)
            )

    def update_throttle(self, direction, dt):
        self.command.throttle += (
            direction
            * self.throttle_speed
            * dt
        )

        self.command.throttle = float(
            np.clip(
                self.command.throttle,
                0.0,
                1.0
            )
        )

    def update(self, dt):
        del dt

        throttle = self.command.throttle

        pitch = (
            self.command.pitch
            * self.max_tilt
        )

        roll = (
            self.command.roll
            * self.max_tilt
        )

        yaw = (
            self.command.yaw
            * self.max_yaw
        )

        pitch_mix = pitch * 0.45
        roll_mix = roll * 0.45
        yaw_mix = yaw * 0.25

        motor_1 = (
            throttle
            + pitch_mix
            - roll_mix
            - yaw_mix
        )

        motor_2 = (
            throttle
            + pitch_mix
            + roll_mix
            + yaw_mix
        )

        motor_3 = (
            throttle
            - pitch_mix
            - roll_mix
            - yaw_mix
        )

        motor_4 = (
            throttle
            - pitch_mix
            + roll_mix
            + yaw_mix
        )

        return np.clip(
            np.array(
                [
                    motor_1,
                    motor_2,
                    motor_3,
                    motor_4,
                ],
                dtype=float
            ),
            0.0,
            1.0
        )

    def reset(self):
        self.command = FlightCommand()

    @property
    def throttle(self):
        return self.command.throttle

    @property
    def pitch(self):
        return self.command.pitch

    @property
    def roll(self):
        return self.command.roll

    @property
    def yaw(self):
        return self.command.yaw