"""Hover Stability and Precision Training Scenario."""

import numpy as np
from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine


def run_hover_training(target_altitude_m: float = 5.0, test_duration_s: float = 20.0):
    print("=" * 60)
    print(f"[*] Starting Hover Stability Training Evaluation")
    print(f"[*] Target Hover Altitude: {target_altitude_m} m")
    print("=" * 60)

    engine = UnifiedFlightEngine()
    engine.arm()
    engine.set_flight_mode("AUTO_TAKEOFF")
    engine.autopilot.takeoff_target_alt = target_altitude_m

    dt = 0.02
    t = 0.0
    alt_errors = []

    while t < test_duration_s:
        engine.update(dt)
        telem = engine.get_telemetry_snapshot()
        alt = telem["position"]["altitude_agl"]

        # Track error after initial climb (t > 4s)
        if t > 4.0:
            alt_errors.append(abs(alt - target_altitude_m))

        if int(t * 50) % 50 == 0:
            print(f"T={t:4.1f}s | Alt={alt:5.2f}m | Target={target_altitude_m:5.2f}m | Error={abs(alt - target_altitude_m):5.2f}m")

        t += dt

    if alt_errors:
        rmse = np.sqrt(np.mean(np.array(alt_errors) ** 2))
        max_err = np.max(alt_errors)
        print("-" * 60)
        print(f"[*] HOVER STABILITY METRICS:")
        print(f"    - Root Mean Square Error (RMSE): {rmse:5.3f} m")
        print(f"    - Maximum Deviation           : {max_err:5.3f} m")
        print(f"    - Stability Rating            : {'EXCELLENT' if rmse < 0.2 else 'GOOD'}")
        print("=" * 60)


if __name__ == "__main__":
    run_hover_training(5.0, 15.0)
