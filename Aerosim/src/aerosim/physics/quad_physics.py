from dataclasses import dataclass
import math

import numpy as np

from aerosim.vehicle.motor import Motor


@dataclass
class DroneState:
    position: np.ndarray
    velocity: np.ndarray
    rotation: np.ndarray
    angular_velocity: np.ndarray


class QuadPhysics:

    def __init__(self):
        self.mass = 1.2
        self.gravity = 9.81

        self.arm_length = 0.23

        self.linear_drag = 0.18
        self.angular_drag = 0.08

        self.inertia = np.array(
            [0.018, 0.018, 0.032],
            dtype=float
        )

        self.state = DroneState(
            position=np.array(
                [0.0, 0.0, 1.0],
                dtype=float
            ),
            velocity=np.zeros(3, dtype=float),
            rotation=np.zeros(3, dtype=float),
            angular_velocity=np.zeros(3, dtype=float),
        )

        self.motors = [
            Motor(1, 1),
            Motor(2, -1),
            Motor(3, 1),
            Motor(4, -1),
        ]

    def set_motors(self, commands):
        commands = np.asarray(
            commands,
            dtype=float
        )

        if commands.shape != (4,):
            raise ValueError(
                "QuadPhysics requires exactly 4 motor commands."
            )

        for motor, command in zip(
            self.motors,
            commands
        ):
            motor.set_command(command)

    def update_motors(self, dt):
        for motor in self.motors:
            motor.update(dt)

    def get_motor_thrust(self):
        return np.array(
            [
                motor.thrust
                for motor in self.motors
            ],
            dtype=float
        )

    def get_motor_rpm(self):
        return np.array(
            [
                motor.rpm
                for motor in self.motors
            ],
            dtype=float
        )

    def calculate_thrust_force(self):

        thrust = np.sum(
            self.get_motor_thrust()
        )

        roll = self.state.rotation[0]
        pitch = self.state.rotation[1]

        force_x = (
            -math.sin(pitch)
            * thrust
        )

        force_y = (
            math.sin(roll)
            * math.cos(pitch)
            * thrust
        )

        force_z = (
            math.cos(roll)
            * math.cos(pitch)
            * thrust
        )

        return np.array(
            [
                force_x,
                force_y,
                force_z
            ],
            dtype=float
        )

    def calculate_total_force(self):

        thrust_force = (
            self.calculate_thrust_force()
        )

        gravity_force = np.array(
            [
                0.0,
                0.0,
                -self.mass * self.gravity
            ],
            dtype=float
        )

        drag_force = (
            -self.linear_drag
            * self.state.velocity
        )

        return (
            thrust_force
            + gravity_force
            + drag_force
        )

    def calculate_torques(self):

        thrusts = self.get_motor_thrust()

        motor_1 = thrusts[0]
        motor_2 = thrusts[1]
        motor_3 = thrusts[2]
        motor_4 = thrusts[3]

        roll_torque = (
            self.arm_length
            * (
                -motor_1
                + motor_2
                + motor_3
                - motor_4
            )
        )

        pitch_torque = (
            self.arm_length
            * (
                motor_1
                + motor_2
                - motor_3
                - motor_4
            )
        )

        yaw_torque = (
            (
                motor_1
                - motor_2
                + motor_3
                - motor_4
            )
            * 0.02
        )

        return np.array(
            [
                roll_torque,
                pitch_torque,
                yaw_torque
            ],
            dtype=float
        )

    def update(self, dt):

        dt = max(
            0.0001,
            min(dt, 0.05)
        )

        self.update_motors(dt)

        total_force = (
            self.calculate_total_force()
        )

        acceleration = (
            total_force
            / self.mass
        )

        self.state.velocity += (
            acceleration * dt
        )

        self.state.position += (
            self.state.velocity * dt
        )

        torques = (
            self.calculate_torques()
        )

        angular_acceleration = (
            torques
            / self.inertia
        )

        angular_acceleration -= (
            self.angular_drag
            * self.state.angular_velocity
        )

        self.state.angular_velocity += (
            angular_acceleration * dt
        )

        self.state.rotation += (
            self.state.angular_velocity * dt
        )

        self.state.rotation = (
            self.state.rotation + math.pi
        ) % (2.0 * math.pi) - math.pi

        if self.state.position[2] < 0.15:

            self.state.position[2] = 0.15

            if self.state.velocity[2] < 0.0:
                self.state.velocity[2] = 0.0

            self.state.angular_velocity *= 0.92

    def reset(self):

        self.state.position[:] = [
            0.0,
            0.0,
            1.0
        ]

        self.state.velocity[:] = 0.0
        self.state.rotation[:] = 0.0
        self.state.angular_velocity[:] = 0.0

        for motor in self.motors:
            motor.reset()

    @property
    def altitude(self):
        return float(
            self.state.position[2]
        )

    @property
    def speed(self):
        return float(
            np.linalg.norm(
                self.state.velocity
            )
        )

    @property
    def roll(self):
        return math.degrees(
            self.state.rotation[0]
        )

    @property
    def pitch(self):
        return math.degrees(
            self.state.rotation[1]
        )

    @property
    def yaw(self):
        return math.degrees(
            self.state.rotation[2]
        )

    @property
    def motor_throttle(self):
        return np.array(
            [
                motor.command
                for motor in self.motors
            ],
            dtype=float
        )

    @property
    def motor_rpm(self):
        return self.get_motor_rpm()

    @property
    def motor_thrust(self):
        return self.get_motor_thrust()