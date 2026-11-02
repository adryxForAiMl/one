from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import time
from aerosim.navigation.geodesy import haversine_distance


class MissionStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class WaypointAction(str, Enum):
    WAYPOINT = "WAYPOINT"
    LOITER = "LOITER"
    LAND = "LAND"
    RTH = "RTH"


@dataclass
class Waypoint:
    id: int
    latitude: float
    longitude: float
    altitude: float  # meters AGL (above ground level)
    speed: float = 5.0  # target cruise speed m/s
    loiter_time: float = 2.0  # seconds to hover at waypoint
    action: WaypointAction = WaypointAction.WAYPOINT


class MissionManager:
    """Manages autonomous flight plans and waypoint sequencing."""
    def __init__(self, acceptance_radius: float = 3.0):
        self.waypoints: List[Waypoint] = []
        self.current_wp_index: int = 0
        self.status: MissionStatus = MissionStatus.IDLE
        self.acceptance_radius = acceptance_radius
        self.loiter_start_time: Optional[float] = None
        self.is_loitering: bool = False
        self.total_distance_m: float = 0.0

    def set_waypoints(self, waypoints_data: List[dict]):
        self.waypoints = []
        for idx, item in enumerate(waypoints_data):
            self.waypoints.append(
                Waypoint(
                    id=idx + 1,
                    latitude=float(item.get("latitude", 0.0)),
                    longitude=float(item.get("longitude", 0.0)),
                    altitude=float(item.get("altitude", 15.0)),
                    speed=float(item.get("speed", 5.0)),
                    loiter_time=float(item.get("loiter_time", 2.0)),
                    action=WaypointAction(item.get("action", "WAYPOINT"))
                )
            )
        self.current_wp_index = 0
        self.status = MissionStatus.IDLE
        self._calculate_total_distance()

    def _calculate_total_distance(self):
        dist = 0.0
        for i in range(len(self.waypoints) - 1):
            wp1 = self.waypoints[i]
            wp2 = self.waypoints[i + 1]
            dist += haversine_distance(wp1.latitude, wp1.longitude, wp2.latitude, wp2.longitude)
        self.total_distance_m = dist

    def start(self) -> bool:
        if not self.waypoints:
            return False
        self.status = MissionStatus.RUNNING
        self.current_wp_index = 0
        self.is_loitering = False
        self.loiter_start_time = None
        return True

    def pause(self):
        if self.status == MissionStatus.RUNNING:
            self.status = MissionStatus.PAUSED

    def resume(self):
        if self.status == MissionStatus.PAUSED:
            self.status = MissionStatus.RUNNING

    def stop(self):
        self.status = MissionStatus.IDLE
        self.current_wp_index = 0
        self.is_loitering = False
        self.loiter_start_time = None

    def clear(self):
        self.stop()
        self.waypoints = []
        self.total_distance_m = 0.0

    def get_target_waypoint(self) -> Optional[Waypoint]:
        if self.status != MissionStatus.RUNNING:
            return None
        if 0 <= self.current_wp_index < len(self.waypoints):
            return self.waypoints[self.current_wp_index]
        return None

    def update(self, current_lat: float, current_lon: float, current_alt: float) -> Optional[Waypoint]:
        """
        Check if current waypoint is reached. If so, handle loiter or advance to next.
        Returns the active target waypoint, or None if completed.
        """
        if self.status != MissionStatus.RUNNING or not self.waypoints:
            return None

        if self.current_wp_index >= len(self.waypoints):
            self.status = MissionStatus.COMPLETED
            return None

        target = self.waypoints[self.current_wp_index]
        horiz_dist = haversine_distance(current_lat, current_lon, target.latitude, target.longitude)
        alt_diff = abs(current_alt - target.altitude)

        # Check if within acceptance sphere
        if horiz_dist <= self.acceptance_radius and alt_diff <= 2.5:
            now = time.time()
            if not self.is_loitering:
                self.is_loitering = True
                self.loiter_start_time = now

            if target.loiter_time <= 0 or (now - self.loiter_start_time) >= target.loiter_time:
                # Proceed to next waypoint
                self.is_loitering = False
                self.loiter_start_time = None
                self.current_wp_index += 1

                if self.current_wp_index >= len(self.waypoints):
                    self.status = MissionStatus.COMPLETED
                    return None
                return self.waypoints[self.current_wp_index]

        return target

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "total_waypoints": len(self.waypoints),
            "current_index": self.current_wp_index,
            "total_distance_m": round(self.total_distance_m, 1),
            "is_loitering": self.is_loitering,
            "waypoints": [
                {
                    "id": wp.id,
                    "latitude": wp.latitude,
                    "longitude": wp.longitude,
                    "altitude": wp.altitude,
                    "speed": wp.speed,
                    "loiter_time": wp.loiter_time,
                    "action": wp.action.value,
                }
                for wp in self.waypoints
            ]
        }
