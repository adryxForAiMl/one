import sys
import time


class CLIDashboard:
    """ASCII Terminal Flight Instrumentation Dashboard."""
    def __init__(self):
        self.last_print = 0.0

    def render(self, telem: dict):
        now = time.time()
        if now - self.last_print < 0.2:  # 5 Hz refresh in terminal
            return
        self.last_print = now

        pos = telem.get("position", {})
        att = telem.get("attitude", {})
        vel = telem.get("velocity", {})
        bat = telem.get("battery", {})
        motors = telem.get("motors", {})
        gps = telem.get("gps", {})

        output = f"""
\033[2J\033[H======================================================================
  🛸 AEROSIM DRONE COCKPIT TELEMETRY - {telem.get('flight_mode', 'N/A')} [{ 'ARMED' if telem.get('is_armed') else 'SAFE' }]
======================================================================
  ALTITUDE AGL : {pos.get('altitude_agl', 0.0):6.2f} m    |  GROUNDSPEED : {vel.get('groundspeed', 0.0):6.2f} m/s
  ALTITUDE MSL : {pos.get('altitude_msl', 0.0):6.2f} m    |  CLIMB RATE  : {vel.get('climb_rate', 0.0):6.2f} m/s
----------------------------------------------------------------------
  ATTITUDE     : ROLL {att.get('roll', 0.0):+5.1f}° | PITCH {att.get('pitch', 0.0):+5.1f}° | YAW {att.get('yaw', 0.0):5.1f}°
  GPS POSITION : LAT {gps.get('latitude', 0.0):9.5f}° | LON {gps.get('longitude', 0.0):9.5f}° ({gps.get('satellites', 0)} Sats)
----------------------------------------------------------------------
  BATTERY      : {bat.get('voltage', 0.0):5.2f} V ({bat.get('percentage', 0.0):3.0f}%) | CURRENT: {bat.get('current', 0.0):5.1f} A
  MOTORS (RPM) : M1:{motors.get('m1_rpm', 0):5d} | M2:{motors.get('m2_rpm', 0):5d} | M3:{motors.get('m3_rpm', 0):5d} | M4:{motors.get('m4_rpm', 0):5d}
======================================================================
"""
        sys.stdout.write(output)
        sys.stdout.flush()
