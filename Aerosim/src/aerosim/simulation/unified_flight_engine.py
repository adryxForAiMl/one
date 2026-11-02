import asyncio
import logging
import math
import time
from typing import Dict, List, Optional
import numpy as np

from aerosim.autopilot.autopilot import DroneAutopilot, FlightMode
from aerosim.hardware.mavlink_bridge import MAVLinkBridge, list_serial_ports
from aerosim.navigation.geodesy import (
    PRESET_LOCATIONS,
    GeoLocation,
    haversine_distance,
    ned_to_gps,
    gps_to_ned,
)
from aerosim.physics.quad_physics import QuadPhysics

logger = logging.getLogger("AeroSim.Engine")


class UnifiedFlightEngine:
    """
    Central Engine for AeroSim supporting both:
    1. Digital Twin Simulation (High-Fidelity 6-DOF Physics + Autopilot)
    2. Real-World Physical Drone Flight (MAVLink over USB Serial / UDP)
    """
    def __init__(self):
        # Operational Mode: 'SIMULATION' or 'HARDWARE'
        self.operation_mode = "SIMULATION"

        # Simulation Subsystems
        self.physics = QuadPhysics()
        self.autopilot = DroneAutopilot()

        # Hardware Subsystem
        self.mavlink = MAVLinkBridge()

        # Current Geo Origin (Default: New York City Manhattan Skyline)
        self.current_location = PRESET_LOCATIONS["new_york"]
        self.autopilot.set_origin(self.current_location)

        # Engine clock & execution
        self.last_update_time = time.time()
        self.is_running = True
        self.flight_time_seconds = 0.0

        # Gimbal camera orientation
        self.gimbal_pitch = -15.0  # degrees
        self.gimbal_yaw = 0.0

    def set_operation_mode(self, mode: str):
        mode = mode.upper()
        if mode in ("SIMULATION", "HARDWARE"):
            self.operation_mode = mode
            logger.info(f"Flight Engine operation mode switched to: {mode}")

    def set_location_preset(self, preset_key: str):
        if preset_key in PRESET_LOCATIONS:
            self.current_location = PRESET_LOCATIONS[preset_key]
            self.autopilot.set_origin(self.current_location)
            self.physics.reset()
            logger.info(f"Geo origin set to preset: {self.current_location.name}")
            return True
        return False

    def set_custom_location(self, name: str, lat: float, lon: float, alt: float):
        loc = GeoLocation(
            name=name,
            city="Custom Coordinates",
            country="Global",
            latitude=lat,
            longitude=lon,
            altitude=alt,
            description=f"User-defined origin: {lat:.6f}, {lon:.6f}"
        )
        self.current_location = loc
        self.autopilot.set_origin(loc)
        self.physics.reset()
        logger.info(f"Custom geo origin set: {lat}, {lon}, alt {alt}")

    def set_wind(self, speed_mps: float, direction_deg: float):
        self.physics.set_wind(speed_mps, direction_deg)

    def set_pilot_sticks(self, throttle: float, pitch: float, roll: float, yaw: float):
        if self.operation_mode == "HARDWARE" and self.mavlink.telemetry.connected:
            self.mavlink.send_rc_override(pitch, roll, throttle, yaw)
        else:
            self.autopilot.set_pilot_input(throttle, pitch, roll, yaw)

    def set_flight_mode(self, mode_str: str) -> bool:
        mode_upper = mode_str.upper()
        if self.operation_mode == "HARDWARE" and self.mavlink.telemetry.connected:
            if mode_upper in ("TAKEOFF", "AUTO_TAKEOFF"):
                return self.mavlink.send_takeoff(5.0)
            elif mode_upper in ("LAND", "AUTO_LAND"):
                return self.mavlink.send_land()
            elif mode_upper in ("RTH", "RTL"):
                return self.mavlink.send_rth()
            elif mode_upper == "ARM":
                return self.mavlink.send_arm(True)
            elif mode_upper == "DISARM":
                return self.mavlink.send_arm(False)
            return True
        else:
            try:
                mode_enum = FlightMode(mode_upper)
                return self.autopilot.set_mode(
                    mode_enum,
                    self.physics.state.position,
                    self.physics.state.rotation[2]
                )
            except ValueError:
                logger.warning(f"Unknown flight mode: {mode_str}")
                return False

    def arm(self) -> bool:
        if self.operation_mode == "HARDWARE":
            return self.mavlink.send_arm(True)
        return self.autopilot.arm()

    def disarm(self) -> bool:
        if self.operation_mode == "HARDWARE":
            return self.mavlink.send_arm(False)
        return self.autopilot.disarm()

    def set_gimbal(self, pitch_deg: float, yaw_deg: float):
        self.gimbal_pitch = float(np.clip(pitch_deg, -90.0, 30.0))
        self.gimbal_yaw = float(np.clip(yaw_deg, -90.0, 90.0))

    def reset_simulation(self):
        self.physics.reset()
        self.autopilot.disarm()
        self.flight_time_seconds = 0.0

    def connect_hardware(self, connection_string: str, baud: int = 115200) -> bool:
        success = self.mavlink.connect(connection_string, baud)
        if success:
            self.operation_mode = "HARDWARE"
        return success

    def disconnect_hardware(self):
        self.mavlink.disconnect()
        self.operation_mode = "SIMULATION"

    def update(self, dt: float):
        dt = max(0.001, min(dt, 0.05))

        if self.operation_mode == "SIMULATION":
            # Autopilot logic loop
            motor_commands, _ = self.autopilot.update(
                dt=dt,
                current_pos=self.physics.state.position,
                current_vel=self.physics.state.velocity,
                current_rot=self.physics.state.rotation,
                current_ang_vel=self.physics.state.angular_velocity
            )

            # Update physics
            self.physics.set_motors(motor_commands)
            self.physics.update(dt)

            if self.autopilot.is_armed and self.physics.altitude > 0.2:
                self.flight_time_seconds += dt

    def get_telemetry_snapshot(self) -> dict:
        now = time.time()

        if self.operation_mode == "HARDWARE" and self.mavlink.telemetry.connected:
            hw = self.mavlink.telemetry
            # In hardware mode, map NED roughly around home origin
            ned_n, ned_e, _ = gps_to_ned(
                hw.latitude, hw.longitude, hw.altitude_msl,
                self.current_location.latitude, self.current_location.longitude, self.current_location.altitude
            )
            dist_home = haversine_distance(
                hw.latitude, hw.longitude,
                self.current_location.latitude, self.current_location.longitude
            )

            return {
                "timestamp": now,
                "operation_mode": "HARDWARE",
                "hardware_connected": True,
                "hardware_port": hw.port_name,
                "autopilot_firmware": hw.autopilot_type,
                "is_armed": hw.is_armed,
                "flight_mode": hw.flight_mode,
                "flight_time": round(self.flight_time_seconds, 1),
                "position": {
                    "north": round(ned_n, 2),
                    "east": round(ned_e, 2),
                    "altitude_agl": round(hw.altitude_relative, 2),
                    "altitude_msl": round(hw.altitude_msl, 2),
                },
                "gps": {
                    "latitude": round(hw.latitude, 7),
                    "longitude": round(hw.longitude, 7),
                    "altitude": round(hw.altitude_msl, 2),
                    "satellites": hw.satellites_visible,
                    "fix_type": hw.gps_fix_type,
                    "distance_to_home": round(dist_home, 1),
                },
                "attitude": {
                    "roll": round(hw.roll_deg, 2),
                    "pitch": round(hw.pitch_deg, 2),
                    "yaw": round(hw.yaw_deg, 2),
                },
                "velocity": {
                    "groundspeed": round(hw.groundspeed, 2),
                    "climb_rate": round(hw.climb_rate, 2),
                },
                "motors": {
                    "m1_rpm": 5200 if hw.is_armed else 0,
                    "m2_rpm": 5200 if hw.is_armed else 0,
                    "m3_rpm": 5200 if hw.is_armed else 0,
                    "m4_rpm": 5200 if hw.is_armed else 0,
                    "thrust_total": 13.5 if hw.is_armed else 0.0,
                },
                "battery": {
                    "voltage": round(hw.battery_voltage, 2),
                    "current": round(hw.battery_current, 2),
                    "percentage": round(hw.battery_remaining, 1),
                },
                "gimbal": {
                    "pitch": self.gimbal_pitch,
                    "yaw": self.gimbal_yaw,
                },
                "origin": {
                    "name": self.current_location.name,
                    "city": self.current_location.city,
                    "latitude": self.current_location.latitude,
                    "longitude": self.current_location.longitude,
                    "altitude": self.current_location.altitude,
                },
                "mission": self.autopilot.mission_mgr.to_dict(),
                "wind": {
                    "speed": 0.0,
                    "direction": 0.0,
                }
            }

        else:
            # SIMULATION MODE
            pos = self.physics.state.position
            vel = self.physics.state.velocity
            rot = self.physics.state.rotation
            rpms = self.physics.get_motor_rpm()
            thrusts = self.physics.get_motor_thrust()

            # Global GPS coordinates
            gps_lat, gps_lon, gps_alt = ned_to_gps(
                pos[0], pos[1], -pos[2],
                self.current_location.latitude,
                self.current_location.longitude,
                self.current_location.altitude
            )

            dist_home = math.sqrt(pos[0] ** 2 + pos[1] ** 2)

            return {
                "timestamp": now,
                "operation_mode": "SIMULATION",
                "hardware_connected": self.mavlink.telemetry.connected,
                "hardware_port": self.mavlink.telemetry.port_name,
                "autopilot_firmware": "AeroSim-Core-v2.0",
                "is_armed": self.autopilot.is_armed,
                "flight_mode": self.autopilot.mode.value,
                "flight_time": round(self.flight_time_seconds, 1),
                "position": {
                    "north": round(float(pos[0]), 2),
                    "east": round(float(pos[1]), 2),
                    "altitude_agl": round(float(pos[2]), 2),
                    "altitude_msl": round(float(gps_alt), 2),
                },
                "gps": {
                    "latitude": round(float(gps_lat), 7),
                    "longitude": round(float(gps_lon), 7),
                    "altitude": round(float(gps_alt), 2),
                    "satellites": 19,
                    "fix_type": 3,
                    "distance_to_home": round(dist_home, 1),
                },
                "attitude": {
                    "roll": round(math.degrees(rot[0]), 2),
                    "pitch": round(math.degrees(rot[1]), 2),
                    "yaw": round((math.degrees(rot[2]) + 360.0) % 360.0, 2),
                },
                "velocity": {
                    "vx": round(float(vel[0]), 2),
                    "vy": round(float(vel[1]), 2),
                    "vz": round(float(vel[2]), 2),
                    "groundspeed": round(float(math.sqrt(vel[0]**2 + vel[1]**2)), 2),
                    "airspeed": round(self.physics.speed, 2),
                    "climb_rate": round(float(vel[2]), 2),
                },
                "motors": {
                    "m1_rpm": round(float(rpms[0])),
                    "m2_rpm": round(float(rpms[1])),
                    "m3_rpm": round(float(rpms[2])),
                    "m4_rpm": round(float(rpms[3])),
                    "m1_thrust": round(float(thrusts[0]), 2),
                    "m2_thrust": round(float(thrusts[1]), 2),
                    "m3_thrust": round(float(thrusts[2]), 2),
                    "m4_thrust": round(float(thrusts[3]), 2),
                    "thrust_total": round(float(np.sum(thrusts)), 2),
                },
                "battery": {
                    "voltage": round(self.physics.battery.voltage, 2),
                    "current": round(self.physics.battery.current_a, 2),
                    "percentage": round(self.physics.battery.percentage, 1),
                    "remaining_mah": round(self.physics.battery.remaining_mah, 0),
                },
                "gimbal": {
                    "pitch": self.gimbal_pitch,
                    "yaw": self.gimbal_yaw,
                },
                "origin": {
                    "name": self.current_location.name,
                    "city": self.current_location.city,
                    "latitude": self.current_location.latitude,
                    "longitude": self.current_location.longitude,
                    "altitude": self.current_location.altitude,
                },
                "mission": self.autopilot.mission_mgr.to_dict(),
                "wind": {
                    "speed": round(self.physics.wind_speed, 1),
                    "direction": round(self.physics.wind_direction, 0),
                }
            }
