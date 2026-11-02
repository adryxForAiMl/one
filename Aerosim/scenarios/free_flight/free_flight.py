"""Free Flight Scenario with crosswinds and gust spectrum."""

import time
from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine


def run_free_flight_scenario(duration_seconds: float = 30.0, wind_speed: float = 4.5):
    print("=" * 60)
    print(f"[*] Starting Free Flight Scenario ({duration_seconds}s)")
    print(f"[*] Setting Crosswind: {wind_speed} m/s at 270 degrees (West Wind)")
    print("=" * 60)

    engine = UnifiedFlightEngine()
    engine.set_wind(wind_speed, 270.0)

    # Arm and Takeoff
    engine.arm()
    engine.set_flight_mode("AUTO_TAKEOFF")

    dt = 0.02
    t = 0.0
    while t < duration_seconds:
        engine.update(dt)
        if int(t * 50) % 50 == 0:  # Every 1 second
            telem = engine.get_telemetry_snapshot()
            pos = telem["position"]
            att = telem["attitude"]
            print(f"T={t:4.1f}s | Mode={telem['flight_mode']} | Alt={pos['altitude_agl']:5.2f}m | Roll={att['roll']:+5.1f}° | Pitch={att['pitch']:+5.1f}° | Battery={telem['battery']['percentage']:4.1f}%")
        t += dt
        time.sleep(0.002)

    print("[*] Free flight completed successfully.")


if __name__ == "__main__":
    run_free_flight_scenario(10.0)
