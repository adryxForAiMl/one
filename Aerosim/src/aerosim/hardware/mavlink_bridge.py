import asyncio
import logging
import math
import sys
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    from pymavlink import mavutil
    PYMAVLINK_AVAILABLE = True
except ImportError:
    PYMAVLINK_AVAILABLE = False

logger = logging.getLogger("AeroSim.MAVLink")


@dataclass
class HardwareTelemetry:
    connected: bool = False
    connection_type: str = "NONE"  # SERIAL, UDP, SITL
    port_name: str = ""
    system_id: int = 1
    autopilot_type: str = "Unknown"
    flight_mode: str = "DISARMED"
    is_armed: bool = False
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_msl: float = 0.0
    altitude_relative: float = 0.0
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    groundspeed: float = 0.0
    climb_rate: float = 0.0
    battery_voltage: float = 0.0
    battery_current: float = 0.0
    battery_remaining: float = 100.0
    satellites_visible: int = 0
    gps_fix_type: int = 0
    last_heartbeat_time: float = 0.0
    packets_received: int = 0


def list_serial_ports() -> List[Dict[str, str]]:
    """Scan and list all available USB/Serial COM ports."""
    ports = []
    if not SERIAL_AVAILABLE:
        return ports

    try:
        available = serial.tools.list_ports.comports()
        for p in available:
            ports.append({
                "device": p.device,
                "description": p.description or p.device,
                "hwid": p.hwid or ""
            })
    except Exception as e:
        logger.warning(f"Error enumerating serial ports: {e}")

    return ports


class MAVLinkBridge:
    """
    Bi-directional MAVLink interface to connect AeroSim with:
    1. Real physical drones (Pixhawk, ArduPilot, PX4) via USB/Serial or Telemetry Radio.
    2. Real network drones or SITL simulators via UDP.
    3. External GCS like QGroundControl via UDP broadcast.
    """
    def __init__(self):
        self.telemetry = HardwareTelemetry()
        self.mav_connection: Optional[mavutil.mavfile] = None
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.broadcast_socket: Optional[mavutil.mavfile] = None

    def connect(self, connection_string: str, baudrate: int = 115200) -> bool:
        """
        Connect to a physical drone via serial port (e.g. '/dev/cu.usbserial-110')
        or UDP (e.g. 'udpin:0.0.0.0:14550' or 'udp:127.0.0.1:14550').
        """
        if not PYMAVLINK_AVAILABLE:
            logger.error("pymavlink is not installed.")
            return False

        self.disconnect()

        try:
            logger.info(f"Connecting MAVLink to {connection_string} (baud: {baudrate})...")
            if "udp" in connection_string.lower():
                self.mav_connection = mavutil.mavlink_connection(connection_string)
                self.telemetry.connection_type = "UDP"
            else:
                self.mav_connection = mavutil.mavlink_connection(
                    connection_string,
                    baud=baudrate,
                    autoreconnect=True
                )
                self.telemetry.connection_type = "SERIAL"

            self.telemetry.port_name = connection_string
            self.is_running = True
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
            return True

        except Exception as e:
            logger.error(f"Failed to connect MAVLink to {connection_string}: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        if self.mav_connection:
            try:
                self.mav_connection.close()
            except Exception:
                pass
            self.mav_connection = None

        with self._lock:
            self.telemetry.connected = False
            self.telemetry.connection_type = "NONE"

    def _read_loop(self):
        """Background thread continuously processing incoming MAVLink packets from real drone."""
        while self.is_running and self.mav_connection:
            try:
                msg = self.mav_connection.recv_match(blocking=True, timeout=0.1)
                if not msg:
                    continue

                msg_type = msg.get_type()
                now = time.time()

                with self._lock:
                    self.telemetry.packets_received += 1

                    if msg_type == "HEARTBEAT":
                        self.telemetry.connected = True
                        self.telemetry.last_heartbeat_time = now
                        self.telemetry.system_id = msg.get_srcSystem()
                        self.telemetry.is_armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

                        # Detect autopilot
                        if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
                            self.telemetry.autopilot_type = "ArduPilot"
                        elif msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_PX4:
                            self.telemetry.autopilot_type = "PX4"
                        else:
                            self.telemetry.autopilot_type = f"MAVLink ({msg.autopilot})"

                    elif msg_type == "GLOBAL_POSITION_INT":
                        self.telemetry.latitude = msg.lat / 1e7
                        self.telemetry.longitude = msg.lon / 1e7
                        self.telemetry.altitude_msl = msg.alt / 1000.0
                        self.telemetry.altitude_relative = msg.relative_alt / 1000.0
                        vx = msg.vx / 100.0
                        vy = msg.vy / 100.0
                        self.telemetry.groundspeed = math.sqrt(vx * vx + vy * vy)
                        self.telemetry.climb_rate = -msg.vz / 100.0
                        if msg.hdg != 65535:
                            self.telemetry.yaw_deg = msg.hdg / 100.0

                    elif msg_type == "ATTITUDE":
                        self.telemetry.roll_deg = math.degrees(msg.roll)
                        self.telemetry.pitch_deg = math.degrees(msg.pitch)
                        self.telemetry.yaw_deg = (math.degrees(msg.yaw) + 360.0) % 360.0

                    elif msg_type == "SYS_STATUS":
                        self.telemetry.battery_voltage = msg.voltage_battery / 1000.0
                        self.telemetry.battery_current = msg.current_battery / 100.0 if msg.current_battery != -1 else 0.0
                        self.telemetry.battery_remaining = float(msg.battery_remaining) if msg.battery_remaining != -1 else 100.0

                    elif msg_type == "GPS_RAW_INT":
                        self.telemetry.satellites_visible = getattr(msg, "satellites_visible", 0)
                        self.telemetry.gps_fix_type = getattr(msg, "fix_type", 0)

                    elif msg_type == "VFR_HUD":
                        self.telemetry.groundspeed = getattr(msg, "groundspeed", self.telemetry.groundspeed)
                        self.telemetry.climb_rate = getattr(msg, "climb", self.telemetry.climb_rate)

                # Check heartbeat timeout
                if now - self.telemetry.last_heartbeat_time > 4.0:
                    self.telemetry.connected = False

            except Exception as e:
                logger.debug(f"MAVLink receive exception: {e}")
                time.sleep(0.05)

    def send_arm(self, arm: bool = True):
        """Arm or disarm the physical drone."""
        if not self.mav_connection:
            return False

        try:
            val = 1.0 if arm else 0.0
            self.mav_connection.mav.command_long_send(
                self.mav_connection.target_system or 1,
                self.mav_connection.target_component or 1,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                val, 0, 0, 0, 0, 0, 0
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send arm command: {e}")
            return False

    def send_takeoff(self, altitude_m: float = 5.0):
        """Send auto-takeoff command to physical drone."""
        if not self.mav_connection:
            return False

        try:
            self.mav_connection.mav.command_long_send(
                self.mav_connection.target_system or 1,
                self.mav_connection.target_component or 1,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0,
                0, 0, 0, 0, 0, 0, altitude_m
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send takeoff command: {e}")
            return False

    def send_land(self):
        """Send auto-land command to physical drone."""
        if not self.mav_connection:
            return False

        try:
            self.mav_connection.mav.command_long_send(
                self.mav_connection.target_system or 1,
                self.mav_connection.target_component or 1,
                mavutil.mavlink.MAV_CMD_NAV_LAND,
                0,
                0, 0, 0, 0, 0, 0, 0
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send land command: {e}")
            return False

    def send_rth(self):
        """Send Return-To-Launch command to physical drone."""
        if not self.mav_connection:
            return False

        try:
            self.mav_connection.mav.command_long_send(
                self.mav_connection.target_system or 1,
                self.mav_connection.target_component or 1,
                mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                0,
                0, 0, 0, 0, 0, 0, 0
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send RTH command: {e}")
            return False

    def send_rc_override(self, pitch: float, roll: float, throttle: float, yaw: float):
        """
        Send raw RC stick override to physical drone.
        Input values normalized [-1.0, 1.0] for roll/pitch/yaw, [0.0, 1.0] for throttle.
        Maps to standard PWM [1000 - 2000] with 1500 center.
        """
        if not self.mav_connection:
            return False

        try:
            pwm_roll = int(1500 + roll * 500)
            pwm_pitch = int(1500 - pitch * 500)
            pwm_throttle = int(1000 + throttle * 1000)
            pwm_yaw = int(1500 + yaw * 500)

            self.mav_connection.mav.rc_channels_override_send(
                self.mav_connection.target_system or 1,
                self.mav_connection.target_component or 1,
                pwm_roll,
                pwm_pitch,
                pwm_throttle,
                pwm_yaw,
                0, 0, 0, 0
            )
            return True
        except Exception as e:
            logger.debug(f"RC override send error: {e}")
            return False

    def get_telemetry_dict(self) -> dict:
        with self._lock:
            return {
                "connected": self.telemetry.connected,
                "connection_type": self.telemetry.connection_type,
                "port_name": self.telemetry.port_name,
                "system_id": self.telemetry.system_id,
                "autopilot": self.telemetry.autopilot_type,
                "is_armed": self.telemetry.is_armed,
                "latitude": self.telemetry.latitude,
                "longitude": self.telemetry.longitude,
                "altitude_msl": round(self.telemetry.altitude_msl, 2),
                "altitude_relative": round(self.telemetry.altitude_relative, 2),
                "roll": round(self.telemetry.roll_deg, 1),
                "pitch": round(self.telemetry.pitch_deg, 1),
                "yaw": round(self.telemetry.yaw_deg, 1),
                "speed": round(self.telemetry.groundspeed, 2),
                "climb_rate": round(self.telemetry.climb_rate, 2),
                "battery_voltage": round(self.telemetry.battery_voltage, 2),
                "battery_current": round(self.telemetry.battery_current, 2),
                "battery_pct": round(self.telemetry.battery_remaining, 1),
                "satellites": self.telemetry.satellites_visible,
                "packets_received": self.telemetry.packets_received,
            }
