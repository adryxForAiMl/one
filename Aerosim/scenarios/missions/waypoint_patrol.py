"""Autonomous Waypoint Patrol Mission Scenario."""

import json
from pathlib import Path
from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine


def run_patrol_mission(mission_file: str = "configs/missions/delhi_survey.json"):
    print("=" * 60)
    print(f"[*] Starting Autonomous Patrol Mission: {mission_file}")
    print("=" * 60)

    engine = UnifiedFlightEngine()

    # Load waypoints
    with open(mission_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    waypoints = config.get("waypoints", [])
    engine.autopilot.mission_mgr.set_waypoints(waypoints)

    engine.arm()
    engine.set_flight_mode("AUTO_TAKEOFF")

    dt = 0.02
    t = 0.0
    switched_to_mission = False

    while t < 60.0:
        engine.update(dt)

        telem = engine.get_telemetry_snapshot()
        alt = telem["position"]["altitude_agl"]

        # Once reaching takeoff altitude, start mission
        if alt > 4.5 and not switched_to_mission:
            print("[*] Reached takeoff altitude. Engaging MISSION mode...")
            engine.set_flight_mode("MISSION")
            switched_to_mission = True

        if int(t * 50) % 50 == 0:
            m_info = telem.get("mission", {})
            print(f"T={t:4.1f}s | Mode={telem['flight_mode']} | WP Index={m_info.get('current_index')}/{m_info.get('total_waypoints')} | Alt={alt:5.2f}m")

        if telem["flight_mode"] in ("AUTO_LAND", "DISARMED") and switched_to_mission:
            print("[*] Mission execution finished!")
            break

        t += dt

    print("[*] Patrol mission scenario completed.")


if __name__ == "__main__":
    run_patrol_mission()
