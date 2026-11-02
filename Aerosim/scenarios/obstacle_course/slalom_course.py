"""Obstacle Slalom Navigation Scenario using AI Avoidance."""

import numpy as np
from aerosim.ai.path_planner import ObstacleAvoidanceAI
from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine


def run_slalom_obstacle_course():
    print("=" * 60)
    print("[*] Starting Slalom Obstacle Course Navigation")
    print("=" * 60)

    # 3 Cylindrical Obstacle Towers (x, y, z, radius)
    obstacles = [
        (10.0, 0.0, 5.0, 2.0),
        (20.0, 3.0, 5.0, 2.0),
        (30.0, -3.0, 5.0, 2.0),
    ]

    ai_planner = ObstacleAvoidanceAI(safe_distance_m=4.5)
    target_destination = np.array([40.0, 0.0, 5.0])

    engine = UnifiedFlightEngine()
    engine.arm()
    engine.set_flight_mode("POS_HOLD")
    engine.autopilot.target_alt = 5.0

    print(f"[*] Navigating through {len(obstacles)} obstacle towers to target {target_destination}...")

    dt = 0.02
    t = 0.0
    while t < 25.0:
        engine.update(dt)
        drone_pos = engine.physics.state.position

        # Compute AI avoidance velocity vector
        avoidance_vel = ai_planner.compute_avoidance_vector(drone_pos, target_destination, obstacles)

        # Feed to position target
        engine.autopilot.target_north += avoidance_vel[0] * dt
        engine.autopilot.target_east += avoidance_vel[1] * dt

        dist_to_goal = np.linalg.norm(drone_pos - target_destination)

        if int(t * 50) % 50 == 0:
            print(f"T={t:4.1f}s | Pos=({drone_pos[0]:5.1f}, {drone_pos[1]:5.1f}, {drone_pos[2]:5.1f}) | Dist to Goal: {dist_to_goal:5.2f}m")

        if dist_to_goal < 2.0:
            print("[*] Goal reached safely without collision!")
            break

        t += dt

    print("[*] Slalom obstacle course scenario complete.")


if __name__ == "__main__":
    run_slalom_obstacle_course()
