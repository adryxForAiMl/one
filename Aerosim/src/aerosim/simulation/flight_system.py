from aerosim.physics.quad_physics import QuadPhysics
from aerosim.control.flight_controller import FlightController
from aerosim.control.keyboard import KeyboardController
from aerosim.vehicle.drone_model import DroneModel


class FlightSystem:

    def __init__(self, base):
        self.base = base

        self.physics = QuadPhysics()
        self.controller = FlightController()

        self.drone = DroneModel(
            self.base.render
        )

        self.keyboard = KeyboardController(
            self.base,
            self.controller
        )

        self.drone.set_transform(
            self.physics.state.position,
            self.physics.state.rotation
        )

    def update(self, dt):

        self.keyboard.update(dt)

        motor_commands = self.controller.update(dt)

        self.physics.set_motors(
            motor_commands
        )

        self.physics.update(dt)

        self.drone.set_transform(
            self.physics.state.position,
            self.physics.state.rotation
        )

        self.drone.update_propellers(
            self.physics.motor_rpm
        )

    def reset(self):

        self.physics.reset()
        self.controller.reset()
        self.keyboard.reset()

        self.drone.reset()

        self.drone.set_transform(
            self.physics.state.position,
            self.physics.state.rotation
        )

    @property
    def position(self):
        return self.physics.state.position.copy()

    @property
    def velocity(self):
        return self.physics.state.velocity.copy()

    @property
    def altitude(self):
        return self.physics.altitude

    @property
    def speed(self):
        return self.physics.speed

    @property
    def roll(self):
        return self.physics.roll

    @property
    def pitch(self):
        return self.physics.pitch

    @property
    def yaw(self):
        return self.physics.yaw

    @property
    def throttle(self):
        return self.controller.throttle

    @property
    def motors(self):
        return self.physics.motor_throttle.copy()

    @property
    def motor_rpm(self):
        return self.physics.motor_rpm.copy()

    @property
    def motor_thrust(self):
        return self.physics.motor_thrust.copy()