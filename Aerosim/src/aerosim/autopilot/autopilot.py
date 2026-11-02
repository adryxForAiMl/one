from dataclasses import dataclass
from enum import Enum
import math
from typing import Optional, Tuple
import numpy as np

from aerosim.autopilot.pid import PIDController
from aerosim.missions.mission_manager import MissionManager
from aerosim.navigation.geodesy import (
    bearing_to,
    haversine_distance,
    gps_to_ned,
    ned_to_gps,
    PRESET_LOCATIONS,
    GeoLocation
)


class FlightMode(str, Enum):
    DISARMED = "DISARMED"
    MANUAL = "MANUAL"
    STABILIZE = "STABILIZE"
    ALT_HOLD = "ALT_HOLD"
    POS_HOLD = "POS_HOLD"
    AUTO_TAKEOFF = "AUTO_TAKEOFF"
    AUTO_LAND = "AUTO_LAND"
    RTH = "RTH"
    MISSION = "MISSION"


@dataclass
class PilotCommands:
    throttle: float = 0.0  # 0.0 to 1.0 (or -1.0 to 1.0 rate in alt_hold)
    pitch: float = 0.0     # -1.0 to 1.0 (Forward/Back)
    roll: float = 0.0      # -1.0 to 1.0 (Left/Right)
    yaw: float = 0.0       # -1.0 to 1.0 (Rotate)


class DroneAutopilot:
    """
    Multi-mode Flight Controller and Autopilot supporting:
    - Manual / Stabilize / Alt Hold / Pos Hold
    - Autonomous Takeoff, Precision Landing, Return-To-Home (RTH)
    - Autonomous Real-World GPS Waypoint Missions
    """
    def __init__(self, origin_location: Optional[GeoLocation] = None):
        if origin_location is None:
            self.origin = PRESET_LOCATIONS["new_delhi"]
        else:
            self.origin = origin_location

        self.mode: FlightMode = FlightMode.DISARMED
        self.is_armed: bool = False

        # Home location for RTH
        self.home_lat: float = self.origin.latitude
        self.home_lon: float = self.origin.longitude
        self.home_alt: float = self.origin.altitude

        # Target Setpoints
        self.target_alt: float = 0.0
        self.target_north: float = 0.0
        self.target_east: float = 0.0
        self.target_yaw: float = 0.0

        # Autonomous flight state
        self.takeoff_target_alt: float = 8.0
        self.rth_safe_alt: float = 15.0
        self.land_speed: float = 0.7  # m/s descent
        self.mission_speed: float = 5.0  # m/s cruise

        # Mission Manager
        self.mission_mgr = MissionManager()

        # PID Controllers
        # Altitude PID: Input (target_alt - current_alt), Output: throttle bias [0.2 to 0.9]
        self.pid_alt = PIDController(kp=0.35, ki=0.12, kd=0.25, output_min=-0.4, output_max=0.4)
        
        # Position PIDs (NED): Input: position error, Output: desired pitch/roll angles (rad)
        self.pid_pos_north = PIDController(kp=0.22, ki=0.03, kd=0.30, output_min=-0.35, output_max=0.35)
        self.pid_pos_east = PIDController(kp=0.22, ki=0.03, kd=0.30, output_min=-0.35, output_max=0.35)

        # Attitude Angle PIDs: Input: desired angle - current angle, Output: control stick
        self.pid_roll = PIDController(kp=3.8, ki=0.2, kd=0.8, output_min=-0.8, output_max=0.8)
        self.pid_pitch = PIDController(kp=3.8, ki=0.2, kd=0.8, output_min=-0.8, output_max=0.8)
        self.pid_yaw = PIDController(kp=2.2, ki=0.1, kd=0.4, output_min=-0.6, output_max=0.6)

        # Pilot stick inputs
        self.pilot_cmd = PilotCommands()

        # Hover throttle baseline (roughly equilibrium against gravity)
        self.hover_throttle = 0.52

    def set_origin(self, loc: GeoLocation):
        self.origin = loc
        self.home_lat = loc.latitude
        self.home_lon = loc.longitude
        self.home_alt = loc.altitude

    def arm(self) -> bool:
        self.is_armed = True
        if self.mode == FlightMode.DISARMED:
            # Default to easy assisted flight (POS_HOLD) instead of raw manual
            self.mode = FlightMode.POS_HOLD
        return True

    def disarm(self) -> bool:
        self.is_armed = False
        self.mode = FlightMode.DISARMED
        return True

    def set_mode(self, new_mode: FlightMode, current_pos: np.ndarray, current_yaw: float) -> bool:
        if not self.is_armed and new_mode not in (FlightMode.DISARMED,):
            # Auto-arm if commanded to fly
            self.arm()

        # Update setpoints upon mode entry
        if new_mode in (FlightMode.ALT_HOLD, FlightMode.POS_HOLD):
            self.target_alt = max(0.5, float(current_pos[2]))
            self.target_north = float(current_pos[0])
            self.target_east = float(current_pos[1])
            self.target_yaw = current_yaw

        elif new_mode == FlightMode.AUTO_TAKEOFF:
            self.target_alt = max(5.0, self.takeoff_target_alt)
            self.target_north = float(current_pos[0])
            self.target_east = float(current_pos[1])
            self.target_yaw = current_yaw

        elif new_mode == FlightMode.RTH:
            # Safe return altitude
            self.target_alt = max(float(current_pos[2]), self.rth_safe_alt)
            self.target_north = 0.0  # Home is at (0, 0)
            self.target_east = 0.0

        elif new_mode == FlightMode.MISSION:
            self.mission_mgr.start()

        self.mode = new_mode
        return True

    def set_pilot_input(self, throttle: float, pitch: float, roll: float, yaw: float):
        self.pilot_cmd.throttle = float(np.clip(throttle, 0.0, 1.0))
        self.pilot_cmd.pitch = float(np.clip(pitch, -1.0, 1.0))
        self.pilot_cmd.roll = float(np.clip(roll, -1.0, 1.0))
        self.pilot_cmd.yaw = float(np.clip(yaw, -1.0, 1.0))

    def update(
        self,
        dt: float,
        current_pos: np.ndarray,      # [North, East, Altitude_AGL]
        current_vel: np.ndarray,      # [Vx, Vy, Vz]
        current_rot: np.ndarray,      # [Roll_rad, Pitch_rad, Yaw_rad]
        current_ang_vel: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates motor commands based on current flight mode.
        Returns:
            motor_commands: np.ndarray shape (4,) [0.0, 1.0]
            desired_attitude: np.ndarray [roll_cmd, pitch_cmd, yaw_cmd, throttle_cmd]
        """
        if not self.is_armed or self.mode == FlightMode.DISARMED:
            return np.zeros(4, dtype=float), np.zeros(4, dtype=float)

        alt = float(current_pos[2])
        north = float(current_pos[0])
        east = float(current_pos[1])
        roll = float(current_rot[0])
        pitch = float(current_rot[1])
        yaw = float(current_rot[2])

        # Current GPS
        curr_lat, curr_lon, _ = ned_to_gps(north, east, -alt, self.home_lat, self.home_lon, self.home_alt)

        desired_roll = 0.0
        desired_pitch = 0.0
        desired_yaw_rate = 0.0
        cmd_throttle = self.hover_throttle

        # ========================================================
        # 1. State Machine Flight Modes
        # ========================================================
        if self.mode == FlightMode.MANUAL:
            # Direct stick passthrough
            cmd_throttle = self.pilot_cmd.throttle
            desired_pitch = self.pilot_cmd.pitch * 0.35
            desired_roll = self.pilot_cmd.roll * 0.35
            desired_yaw_rate = self.pilot_cmd.yaw * 0.25

        elif self.mode == FlightMode.STABILIZE:
            # Self-leveling roll and pitch
            cmd_throttle = self.pilot_cmd.throttle
            desired_pitch = self.pilot_cmd.pitch * 0.35
            desired_roll = self.pilot_cmd.roll * 0.35
            desired_yaw_rate = self.pilot_cmd.yaw * 0.25

        elif self.mode == FlightMode.ALT_HOLD:
            # Stick modifies altitude setpoint or climb velocity
            stick_climb = (self.pilot_cmd.throttle - 0.5) * 2.0  # [-1 to 1]
            if abs(stick_climb) > 0.1:
                self.target_alt += stick_climb * 3.0 * dt
                self.target_alt = max(0.5, self.target_alt)

            alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
            cmd_throttle = np.clip(self.hover_throttle + alt_throttle_adj, 0.15, 0.95)

            desired_pitch = self.pilot_cmd.pitch * 0.35
            desired_roll = self.pilot_cmd.roll * 0.35
            desired_yaw_rate = self.pilot_cmd.yaw * 0.25

        elif self.mode == FlightMode.POS_HOLD:
            # Altitude Hold + Position Hold
            # Throttle stick adjusts target altitude
            stick_climb = (self.pilot_cmd.throttle - 0.5) * 2.0
            if abs(stick_climb) > 0.1:
                self.target_alt += stick_climb * 3.0 * dt
                self.target_alt = max(0.5, self.target_alt)

            alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
            cmd_throttle = np.clip(self.hover_throttle + alt_throttle_adj, 0.15, 0.95)

            # Manual stick override shifts target position
            if abs(self.pilot_cmd.pitch) > 0.05 or abs(self.pilot_cmd.roll) > 0.05:
                # Body to NED frame
                cos_y = math.cos(yaw)
                sin_y = math.sin(yaw)
                fwd_cmd = self.pilot_cmd.pitch * 6.0 * dt
                right_cmd = self.pilot_cmd.roll * 6.0 * dt
                self.target_north += fwd_cmd * cos_y - right_cmd * sin_y
                self.target_east += fwd_cmd * sin_y + right_cmd * cos_y

            # Position PID in NED
            target_accel_n = self.pid_pos_north.update(self.target_north, north, dt)
            target_accel_e = self.pid_pos_east.update(self.target_east, east, dt)

            # Transform desired acceleration into body roll & pitch
            cos_y = math.cos(yaw)
            sin_y = math.sin(yaw)
            accel_fwd = target_accel_n * cos_y + target_accel_e * sin_y
            accel_right = -target_accel_n * sin_y + target_accel_e * cos_y

            desired_pitch = np.clip(accel_fwd, -0.35, 0.35)
            desired_roll = np.clip(accel_right, -0.35, 0.35)
            desired_yaw_rate = self.pilot_cmd.yaw * 0.25

        elif self.mode == FlightMode.AUTO_TAKEOFF:
            # Smooth climb to takeoff altitude
            alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
            cmd_throttle = np.clip(self.hover_throttle + alt_throttle_adj + 0.05, 0.2, 0.95)

            # Hold ground launch spot
            target_accel_n = self.pid_pos_north.update(self.target_north, north, dt)
            target_accel_e = self.pid_pos_east.update(self.target_east, east, dt)
            cos_y = math.cos(yaw)
            sin_y = math.sin(yaw)
            desired_pitch = np.clip(target_accel_n * cos_y + target_accel_e * sin_y, -0.15, 0.15)
            desired_roll = np.clip(-target_accel_n * sin_y + target_accel_e * cos_y, -0.15, 0.15)
            desired_yaw_rate = 0.0

            # Transition to POS_HOLD when takeoff target is reached
            if abs(alt - self.target_alt) < 0.3:
                self.mode = FlightMode.POS_HOLD

        elif self.mode == FlightMode.AUTO_LAND:
            # Gentle descent
            self.target_alt = max(0.0, self.target_alt - self.land_speed * dt)
            alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
            cmd_throttle = np.clip(self.hover_throttle * 0.88 + alt_throttle_adj, 0.1, 0.8)

            # Hold spot while descending
            target_accel_n = self.pid_pos_north.update(self.target_north, north, dt)
            target_accel_e = self.pid_pos_east.update(self.target_east, east, dt)
            cos_y = math.cos(yaw)
            sin_y = math.sin(yaw)
            desired_pitch = np.clip(target_accel_n * cos_y + target_accel_e * sin_y, -0.15, 0.15)
            desired_roll = np.clip(-target_accel_n * sin_y + target_accel_e * cos_y, -0.15, 0.15)
            desired_yaw_rate = 0.0

            # Ground touchdown detection
            if alt < 0.22:
                self.disarm()

        elif self.mode == FlightMode.RTH:
            # Climb to safe altitude first if needed
            dist_to_home = math.sqrt(north * north + east * east)
            if alt < (self.rth_safe_alt - 1.0) and dist_to_home > 5.0:
                self.target_alt = self.rth_safe_alt
            
            alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
            cmd_throttle = np.clip(self.hover_throttle + alt_throttle_adj, 0.2, 0.9)

            # Navigate towards Home (0, 0)
            target_accel_n = self.pid_pos_north.update(0.0, north, dt)
            target_accel_e = self.pid_pos_east.update(0.0, east, dt)
            cos_y = math.cos(yaw)
            sin_y = math.sin(yaw)
            desired_pitch = np.clip(target_accel_n * cos_y + target_accel_e * sin_y, -0.3, 0.3)
            desired_roll = np.clip(-target_accel_n * sin_y + target_accel_e * cos_y, -0.3, 0.3)

            # Point nose towards Home
            if dist_to_home > 3.0:
                bearing_rad = math.atan2(-east, -north)
                yaw_diff = (bearing_rad - yaw + math.pi) % (2 * math.pi) - math.pi
                desired_yaw_rate = np.clip(yaw_diff * 0.8, -0.4, 0.4)
            else:
                desired_yaw_rate = 0.0

            # Once within 2.5m of home, start AUTO_LAND
            if dist_to_home < 2.5 and abs(alt - self.rth_safe_alt) < 2.0:
                self.target_north = 0.0
                self.target_east = 0.0
                self.mode = FlightMode.AUTO_LAND

        elif self.mode == FlightMode.MISSION:
            # Waypoint mission navigation
            active_wp = self.mission_mgr.update(curr_lat, curr_lon, alt)
            if active_wp is not None:
                # Convert waypoint GPS to local NED target
                tgt_n, tgt_e, _ = gps_to_ned(
                    active_wp.latitude, active_wp.longitude, active_wp.altitude,
                    self.home_lat, self.home_lon, self.home_alt
                )
                self.target_north = tgt_n
                self.target_east = tgt_e
                self.target_alt = active_wp.altitude

                alt_throttle_adj = self.pid_alt.update(self.target_alt, alt, dt)
                cmd_throttle = np.clip(self.hover_throttle + alt_throttle_adj, 0.2, 0.95)

                target_accel_n = self.pid_pos_north.update(self.target_north, north, dt)
                target_accel_e = self.pid_pos_east.update(self.target_east, east, dt)
                cos_y = math.cos(yaw)
                sin_y = math.sin(yaw)
                desired_pitch = np.clip(target_accel_n * cos_y + target_accel_e * sin_y, -0.35, 0.35)
                desired_roll = np.clip(-target_accel_n * sin_y + target_accel_e * cos_y, -0.35, 0.35)

                # Face direction of waypoint
                bearing_rad = math.atan2(tgt_e - east, tgt_n - north)
                yaw_diff = (bearing_rad - yaw + math.pi) % (2 * math.pi) - math.pi
                desired_yaw_rate = np.clip(yaw_diff * 0.8, -0.4, 0.4)
            else:
                # Mission completed -> hold position or RTH
                self.mode = FlightMode.POS_HOLD

        # ========================================================
        # 2. Inner Attitude Rate & Angle Loop
        # ========================================================
        roll_corr = self.pid_roll.update(desired_roll, roll, dt)
        pitch_corr = self.pid_pitch.update(desired_pitch, pitch, dt)
        yaw_corr = np.clip(desired_yaw_rate, -0.3, 0.3)

        # Mix to 4 motors (X configuration)
        # Motor 1: Front-Left (CW)
        # Motor 2: Front-Right (CCW)
        # Motor 3: Rear-Left (CCW)
        # Motor 4: Rear-Right (CW)
        m1 = cmd_throttle + pitch_corr * 0.35 - roll_corr * 0.35 - yaw_corr * 0.25
        m2 = cmd_throttle + pitch_corr * 0.35 + roll_corr * 0.35 + yaw_corr * 0.25
        m3 = cmd_throttle - pitch_corr * 0.35 - roll_corr * 0.35 + yaw_corr * 0.25
        m4 = cmd_throttle - pitch_corr * 0.35 + roll_corr * 0.35 - yaw_corr * 0.25

        motor_commands = np.clip(np.array([m1, m2, m3, m4], dtype=float), 0.0, 1.0)
        desired_attitude = np.array([desired_roll, desired_pitch, desired_yaw_rate, cmd_throttle], dtype=float)

        return motor_commands, desired_attitude
