from dataclasses import dataclass
import numpy as np


@dataclass
class GimbalOrientation:
    pitch: float = -15.0  # degrees
    yaw: float = 0.0      # degrees
    roll: float = 0.0     # degrees


class GimbalCamera:
    """
    3-Axis Stabilized 4K Camera Gimbal:
    - Pitch range: -90° (nadir down) to +30° (sky up)
    - Yaw range: -120° to +120°
    - Mode: 'FOLLOW' (stabilized to vehicle), 'FPV' (locked to nose), 'POINT_TO_COORDINATE'
    """
    def __init__(self):
        self.orientation = GimbalOrientation()
        self.mode = "FOLLOW"
        self.target_pitch = -15.0
        self.target_yaw = 0.0
        self.slew_rate = 60.0  # degrees per second

    def set_target(self, pitch_deg: float, yaw_deg: float):
        self.target_pitch = float(np.clip(pitch_deg, -90.0, 30.0))
        self.target_yaw = float(np.clip(yaw_deg, -120.0, 120.0))

    def update(self, dt: float, drone_attitude_deg: tuple):
        # Slew towards targets
        max_delta = self.slew_rate * dt
        p_diff = self.target_pitch - self.orientation.pitch
        y_diff = self.target_yaw - self.orientation.yaw

        self.orientation.pitch += float(np.clip(p_diff, -max_delta, max_delta))
        self.orientation.yaw += float(np.clip(y_diff, -max_delta, max_delta))

        # Stabilize roll against drone tilt
        drone_roll, drone_pitch, drone_yaw = drone_attitude_deg
        if self.mode == "FOLLOW":
            self.orientation.roll = 0.0  # Self-leveling roll
        elif self.mode == "FPV":
            self.orientation.roll = drone_roll

    def get_data(self) -> dict:
        return {
            "mode": self.mode,
            "pitch": round(self.orientation.pitch, 1),
            "yaw": round(self.orientation.yaw, 1),
            "roll": round(self.orientation.roll, 1),
        }
