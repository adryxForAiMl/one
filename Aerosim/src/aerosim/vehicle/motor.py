from dataclasses import dataclass


@dataclass
class MotorParameters:
    max_rpm: float = 12000.0
    max_thrust: float = 7.5
    response_time: float = 0.08
    idle_rpm: float = 900.0


class Motor:
    def __init__(
        self,
        motor_id: int,
        direction: int,
        parameters: MotorParameters | None = None,
    ):
        self.motor_id = motor_id
        self.direction = 1 if direction >= 0 else -1

        self.parameters = (
            parameters
            if parameters is not None
            else MotorParameters()
        )

        self.command = 0.0
        self.rpm = self.parameters.idle_rpm
        self.thrust = 0.0

    def set_command(self, command: float):
        self.command = max(
            0.0,
            min(1.0, float(command))
        )

    def update(self, dt: float):
        dt = max(0.0001, min(dt, 0.05))

        target_rpm = (
            self.parameters.idle_rpm
            + (
                self.parameters.max_rpm
                - self.parameters.idle_rpm
            ) * self.command
        )

        response = max(
            0.001,
            self.parameters.response_time
        )

        blend = min(
            1.0,
            dt / response
        )

        self.rpm += (
            target_rpm - self.rpm
        ) * blend

        normalized_rpm = (
            self.rpm /
            self.parameters.max_rpm
        )

        normalized_rpm = max(
            0.0,
            min(1.0, normalized_rpm)
        )

        self.thrust = (
            self.parameters.max_thrust
            * normalized_rpm
            * normalized_rpm
        )

    def reset(self):
        self.command = 0.0
        self.rpm = self.parameters.idle_rpm
        self.thrust = 0.0

    @property
    def torque_direction(self):
        return self.direction