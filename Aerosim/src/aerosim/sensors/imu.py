import math
import numpy as np
from aerosim.interfaces import SensorInterface


class IMUSensor(SensorInterface):
    """
    6-Axis Inertial Measurement Unit (IMU):
    - 3-Axis Accelerometer (m/s^2) with gravity vector and vibration noise
    - 3-Axis Gyroscope (rad/s and deg/s) with bias drift
    """
    def __init__(self, accel_noise: float = 0.05, gyro_noise: float = 0.005):
        self.accel_noise = accel_noise
        self.gyro_noise = gyro_noise
        self.accel = np.zeros(3, dtype=float)
        self.gyro = np.zeros(3, dtype=float)
        self.gyro_bias = np.random.normal(0, 0.002, 3)

    def update(self, dt: float, state) -> dict:
        # Rotations: Roll, Pitch, Yaw
        roll = state.rotation[0]
        pitch = state.rotation[1]

        # Gravity in body frame
        gx = -9.81 * math.sin(pitch)
        gy = 9.81 * math.sin(roll) * math.cos(pitch)
        gz = 9.81 * math.cos(roll) * math.cos(pitch)
        gravity_body = np.array([gx, gy, gz], dtype=float)

        # Body acceleration + gravity + noise
        noise_a = np.random.normal(0, self.accel_noise, 3)
        self.accel = gravity_body + noise_a

        # Angular velocity + bias + noise
        noise_g = np.random.normal(0, self.gyro_noise, 3)
        self.gyro = state.angular_velocity + self.gyro_bias + noise_g

        return self.get_data()

    def get_data(self) -> dict:
        return {
            "accel_x": round(float(self.accel[0]), 3),
            "accel_y": round(float(self.accel[1]), 3),
            "accel_z": round(float(self.accel[2]), 3),
            "gyro_p": round(float(self.gyro[0]), 4),
            "gyro_q": round(float(self.gyro[1]), 4),
            "gyro_r": round(float(self.gyro[2]), 4),
        }
