import math
import numpy as np
from typing import List, Tuple


class ObstacleAvoidanceAI:
    """
    Artificial Potential Field (APF) Real-Time Obstacle Avoidance:
    - Attractive force pulls drone towards target waypoint
    - Repulsive force pushes drone away from detected obstacles
    - Generates collision-free velocity vector
    """
    def __init__(self, safe_distance_m: float = 4.0):
        self.safe_distance = safe_distance_m
        self.k_att = 1.0  # attractive gain
        self.k_rep = 2.5  # repulsive gain

    def compute_avoidance_vector(
        self,
        drone_pos: np.ndarray,
        target_pos: np.ndarray,
        obstacles: List[Tuple[float, float, float, float]]  # (x, y, z, radius)
    ) -> np.ndarray:
        # 1. Attractive force
        diff = target_pos - drone_pos
        dist_to_target = np.linalg.norm(diff)
        if dist_to_target > 0.01:
            f_att = self.k_att * (diff / dist_to_target)
        else:
            f_att = np.zeros(3)

        # 2. Repulsive force from obstacles
        f_rep = np.zeros(3)
        for obs_x, obs_y, obs_z, obs_r in obstacles:
            obs_pos = np.array([obs_x, obs_y, obs_z])
            obs_diff = drone_pos - obs_pos
            dist = np.linalg.norm(obs_diff) - obs_r

            if 0 < dist < self.safe_distance:
                # Repulsive potential: F = k * (1/d - 1/d0) * (1/d^2) * unit_vector
                direction = obs_diff / (np.linalg.norm(obs_diff) + 1e-6)
                mag = self.k_rep * (1.0 / dist - 1.0 / self.safe_distance) * (1.0 / (dist * dist))
                f_rep += mag * direction

        # Resultant velocity vector
        f_total = f_att + f_rep
        norm = np.linalg.norm(f_total)
        if norm > 6.0:  # Cap at max speed 6 m/s
            f_total = (f_total / norm) * 6.0

        return f_total
