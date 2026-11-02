from dataclasses import dataclass
import math
import numpy as np

from aerosim.vehicle.motor import Motor


@dataclass
class DroneState:
    position: np.ndarray          # [North, East, Altitude_AGL] in meters
    velocity: np.ndarray          # [Vx, Vy, Vz] in m/s
    rotation: np.ndarray          # [Roll, Pitch, Yaw] in radians
    angular_velocity: np.ndarray  # [P, Q, R] rad/s


@dataclass
class BatteryState:
    cell_count: int = 4
    capacity_mah: float = 3500.0
    remaining_mah: float = 3500.0
    voltage: float = 16.8        # Full 4S = 4.2V * 4
    current_a: float = 0.5       # Idle avionics current
    percentage: float = 100.0


class QuadPhysics:
    """
    High-fidelity 6-DOF Quadcopter physics model:
    - 6-DOF non-linear rigid body equations of motion
    - 4 independent motor dynamics with thrust curves
    - Aerodynamic drag & ground-effect lift enhancement
    - Ambient wind vector with turbulence gusts
    - Realistic LiPo battery voltage discharge and current draw
    """
    def __init__(self):
        self.mass = 1.35  # kg (medium-sized quadcopter with gimbal & battery)
        self.gravity = 9.81
        self.arm_length = 0.24  # meters

        self.linear_drag = 0.22
        self.angular_drag = 0.12

        self.inertia = np.array(
            [0.022, 0.022, 0.038],
            dtype=float
        )

        self.state = DroneState(
            position=np.array([0.0, 0.0, 0.15], dtype=float),
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

        # Wind & Environment
        self.wind_speed = 0.0  # m/s
        self.wind_direction = 0.0  # degrees (0 = blowing from North)
        self.wind_vector = np.zeros(3, dtype=float)

        # Battery
        self.battery = BatteryState()

    def set_wind(self, speed_mps: float, direction_deg: float):
        self.wind_speed = float(max(0.0, speed_mps))
        self.wind_direction = float(direction_deg % 360.0)
        # Vector towards which wind is blowing
        rad = math.radians((direction_deg + 180.0) % 360.0)
        self.wind_vector = np.array([
            math.cos(rad) * self.wind_speed,
            math.sin(rad) * self.wind_speed,
            0.0
        ], dtype=float)

    def set_motors(self, commands):
        commands = np.asarray(commands, dtype=float)
        if commands.shape != (4,):
            raise ValueError("QuadPhysics requires exactly 4 motor commands.")

        for motor, command in zip(self.motors, commands):
            motor.set_command(command)

    def update_motors(self, dt):
        for motor in self.motors:
            motor.update(dt)

    def get_motor_thrust(self):
        return np.array([motor.thrust for motor in self.motors], dtype=float)

    def get_motor_rpm(self):
        return np.array([motor.rpm for motor in self.motors], dtype=float)

    def _ground_effect_multiplier(self) -> float:
        """Ground effect increases rotor efficiency when very close to surface."""
        alt = max(0.05, float(self.state.position[2]))
        rotor_diam = 0.25  # ~10 inch props
        ratio = alt / (4.0 * rotor_diam)
        if ratio < 1.0:
            return 1.0 + 0.18 * (1.0 - ratio)
        return 1.0

    def calculate_thrust_force(self):
        thrusts = self.get_motor_thrust()
        base_thrust = np.sum(thrusts) * self._ground_effect_multiplier()

        roll = self.state.rotation[0]
        pitch = self.state.rotation[1]
        yaw = self.state.rotation[2]

        # Body Z axis in NED: rotated by Roll, Pitch, Yaw
        # In our NED-like simulation:
        # X: North (+forward), Y: East (+right), Z: Altitude (+up)
        force_x = (math.sin(roll) * math.sin(yaw) + math.cos(roll) * math.sin(pitch) * math.cos(yaw)) * base_thrust
        force_y = (-math.sin(roll) * math.cos(yaw) + math.cos(roll) * math.sin(pitch) * math.sin(yaw)) * base_thrust
        force_z = (math.cos(roll) * math.cos(pitch)) * base_thrust

        return np.array([force_x, force_y, force_z], dtype=float)

    def calculate_total_force(self):
        thrust_force = self.calculate_thrust_force()

        gravity_force = np.array([0.0, 0.0, -self.mass * self.gravity], dtype=float)

        # Relative airspeed considering wind
        apparent_velocity = self.state.velocity - self.wind_vector
        drag_force = -self.linear_drag * apparent_velocity * np.linalg.norm(apparent_velocity)
        if np.isnan(drag_force).any():
            drag_force = np.zeros(3, dtype=float)

        return thrust_force + gravity_force + drag_force

    def calculate_torques(self):
        thrusts = self.get_motor_thrust()
        m1, m2, m3, m4 = thrusts[0], thrusts[1], thrusts[2], thrusts[3]

        # Standard Quad X layout:
        # Front-Left: m1, Front-Right: m2, Rear-Left: m3, Rear-Right: m4
        arm_d = self.arm_length / math.sqrt(2.0)
        roll_torque = arm_d * (-m1 + m2 - m3 + m4)
        pitch_torque = arm_d * (m1 + m2 - m3 - m4)
        # Yaw torque from motor reaction torque
        yaw_torque = (m1 - m2 - m3 + m4) * 0.024

        return np.array([roll_torque, pitch_torque, yaw_torque], dtype=float)

    def update_battery(self, dt: float):
        # Current draw calculation based on motor thrusts
        total_thrust = np.sum(self.get_motor_thrust())
        # Hover is ~13.5 N total (approx 14 Amps). Max thrust ~30N (approx 45 Amps).
        avionics_current = 0.8
        motor_current = (total_thrust / 30.0) ** 1.6 * 44.0
        self.battery.current_a = avionics_current + motor_current

        # Consumed mAh
        consumed_mah = (self.battery.current_a * (dt / 3600.0)) * 1000.0
        self.battery.remaining_mah = max(0.0, self.battery.remaining_mah - consumed_mah)
        self.battery.percentage = max(0.0, min(100.0, (self.battery.remaining_mah / self.battery.capacity_mah) * 100.0))

        # LiPo 4S discharge voltage curve with internal resistance sag
        fraction = self.battery.percentage / 100.0
        nominal_cell_v = 3.3 + 0.9 * (fraction ** 0.5)  # 3.3V (empty) to 4.2V (full)
        internal_resistance = 0.025  # Ohms
        self.battery.voltage = max(12.0, (nominal_cell_v * self.battery.cell_count) - (self.battery.current_a * internal_resistance))

    def update(self, dt):
        dt = max(0.0001, min(dt, 0.05))

        self.update_motors(dt)
        self.update_battery(dt)

        total_force = self.calculate_total_force()
        acceleration = total_force / self.mass

        self.state.velocity += acceleration * dt
        self.state.position += self.state.velocity * dt

        torques = self.calculate_torques()
        angular_acceleration = torques / self.inertia
        angular_acceleration -= self.angular_drag * self.state.angular_velocity

        self.state.angular_velocity += angular_acceleration * dt
        self.state.rotation += self.state.angular_velocity * dt

        # Wrap rotation between -pi and +pi
        self.state.rotation = (self.state.rotation + math.pi) % (2.0 * math.pi) - math.pi

        # Ground collision constraint
        ground_z = 0.15
        if self.state.position[2] <= ground_z:
            self.state.position[2] = ground_z
            if self.state.velocity[2] < 0.0:
                self.state.velocity[2] = 0.0

            # Ground friction
            self.state.velocity[0] *= 0.88
            self.state.velocity[1] *= 0.88
            self.state.angular_velocity *= 0.85

            # If almost zero vertical force and upright on ground, level out
            if np.sum(self.get_motor_thrust()) < (self.mass * self.gravity * 0.7):
                self.state.rotation[0] *= 0.90
                self.state.rotation[1] *= 0.90

    def reset(self):
        self.state.position[:] = [0.0, 0.0, 0.15]
        self.state.velocity[:] = 0.0
        self.state.rotation[:] = 0.0
        self.state.angular_velocity[:] = 0.0

        for motor in self.motors:
            motor.reset()

        self.battery.remaining_mah = self.battery.capacity_mah
        self.battery.percentage = 100.0
        self.battery.voltage = 16.8

    @property
    def altitude(self):
        return float(self.state.position[2])

    @property
    def speed(self):
        return float(np.linalg.norm(self.state.velocity))

    @property
    def roll(self):
        return math.degrees(self.state.rotation[0])

    @property
    def pitch(self):
        return math.degrees(self.state.rotation[1])

    @property
    def yaw(self):
        return (math.degrees(self.state.rotation[2]) + 360.0) % 360.0

    @property
    def motor_throttle(self):
        return np.array([motor.command for motor in self.motors], dtype=float)

    @property
    def motor_rpm(self):
        return self.get_motor_rpm()

    @property
    def motor_thrust(self):
        return self.get_motor_thrust()