"""Discrete-time traffic queue evolution model and accumulation dynamics.

Implements:
1. First-principles hydrodynamic point-queue model:
       q_i(k+1) = max(0, q_i(k) + a_i(k) - d_i(k))
2. Time-continuous integration of delay using composite trapezoidal rule:
       D_i(T) = \int_0^T q_i(t) dt
3. Forward prediction of queue trajectories for rolling-horizon signal optimization.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from Traffic.backend.numerical_methods import trapezoidal_rule, trapezoidal_cumulative


@dataclass
class MovementState:
    """State of an intersection movement or lane group."""
    movement_id: str
    name: str
    saturation_flow: float = 0.50     # veh/sec (approx 1800 veh/hr/lane)
    arrival_rate: float = 0.15        # veh/sec (approx 540 veh/hr)
    capacity: int = 40                # Maximum storage capacity (vehicles) before spillback
    weight: float = 1.0               # Priority / penalty weight in objective function
    
    # Dynamic state
    current_queue: float = 0.0
    is_green: bool = False
    
    # Historical telemetry
    time_history: List[float] = field(default_factory=list)
    queue_history: List[float] = field(default_factory=list)
    arrival_history: List[float] = field(default_factory=list)
    departure_history: List[float] = field(default_factory=list)
    green_history: List[bool] = field(default_factory=list)

    def step(self, dt: float, is_green: bool, external_arrivals: Optional[float] = None) -> Tuple[float, float]:
        """Advance movement state by discrete time interval dt (seconds).
        
        Queue evolution:
            arrivals = external_arrivals if provided else arrival_rate * dt
            departures = saturation_flow * dt if is_green else 0
            q_{k+1} = max(0, q_k + arrivals - departures)
            
        Returns:
            Tuple[float, float]: (arrivals, actual_departures)
        """
        self.is_green = is_green
        arrivals = external_arrivals if external_arrivals is not None else (self.arrival_rate * dt)
        
        # Max departures possible during green
        potential_departures = (self.saturation_flow * dt) if is_green else 0.0
        
        # Actual departures cannot exceed available queue + arrivals in current step
        actual_departures = min(self.current_queue + arrivals, potential_departures)
        
        # Queue update with non-negativity constraint
        new_queue = max(0.0, self.current_queue + arrivals - actual_departures)
        new_queue = min(float(self.capacity), new_queue)  # Spillback ceiling
        
        self.current_queue = new_queue
        
        t_now = self.time_history[-1] + dt if self.time_history else 0.0
        self.time_history.append(t_now)
        self.queue_history.append(new_queue)
        self.arrival_history.append(arrivals)
        self.departure_history.append(actual_departures)
        self.green_history.append(is_green)
        
        return arrivals, actual_departures

    def get_accumulated_delay(self) -> float:
        """Compute accumulated vehicle-seconds of delay via Trapezoidal rule:
            D = \int_0^T q(t) dt \approx \sum 0.5 * (q_k + q_{k+1}) * \Delta t
        """
        if len(self.queue_history) < 2:
            return 0.0
        return trapezoidal_rule(np.array(self.queue_history), np.array(self.time_history))

    def get_cumulative_delay_curve(self) -> np.ndarray:
        """Return running cumulative delay curve over time."""
        if len(self.queue_history) < 2:
            return np.zeros(len(self.queue_history))
        return trapezoidal_cumulative(np.array(self.queue_history), np.array(self.time_history))

    def predict_trajectory(
        self,
        horizon: float,
        green_time: float,
        cycle_length: float,
        dt: float = 1.0
    ) -> np.ndarray:
        """Simulate forward in time to evaluate total delay for a candidate green duration.
        
        In a standard cycle, green is active for [0, green_time), and red for [green_time, cycle_length).
        Repeats periodically over the given horizon.
        """
        steps = int(horizon / dt)
        predicted_q = np.zeros(steps + 1)
        predicted_q[0] = self.current_queue
        
        q = self.current_queue
        for k in range(steps):
            t = (k * dt) % cycle_length
            green = (t < green_time)
            arrivals = self.arrival_rate * dt
            dep_cap = (self.saturation_flow * dt) if green else 0.0
            dep = min(q + arrivals, dep_cap)
            q = max(0.0, q + arrivals - dep)
            predicted_q[k + 1] = q
            
        return predicted_q


class IntersectionQueueModel:
    """Coordinated multi-phase intersection queue system.
    
    Standard 4-approach or 2-phase/4-phase intersection:
    - Phase 1 (N-S): Movements North & South
    - Phase 2 (E-W): Movements East & West
    """
    def __init__(self, movement_ids: Optional[List[str]] = None):
        if movement_ids is None:
            movement_ids = ["North", "South", "East", "West"]
            
        self.movements: Dict[str, MovementState] = {
            m_id: MovementState(
                movement_id=m_id,
                name=f"{m_id} Approach",
                saturation_flow=0.50,  # 1800 veh/hr/lane
                arrival_rate=0.15 if m_id in ["North", "South"] else 0.10,
                capacity=50,
                weight=1.0
            )
            for m_id in movement_ids
        }
        
        # Phase mappings: which movements receive green in each phase
        self.phase_to_movements = {
            0: ["North", "South"],  # N-S Arterial phase
            1: ["East", "West"]     # E-W Collector phase
        }

    def reset(self):
        """Reset all historical telemetry and queue states."""
        for m in self.movements.values():
            m.current_queue = 0.0
            m.is_green = False
            m.time_history.clear()
            m.queue_history.clear()
            m.arrival_history.clear()
            m.departure_history.clear()
            m.green_history.clear()

    def update_from_sensors(self, sensor_queues: Dict[str, float], active_phase: int):
        """Synchronize queue state from external SUMO loop/area detectors or TraCI."""
        green_movements = self.phase_to_movements.get(active_phase, [])
        for m_id, m in self.movements.items():
            if m_id in sensor_queues:
                m.current_queue = sensor_queues[m_id]
            m.is_green = (m_id in green_movements)

    def step(self, dt: float, active_phase: int, arrivals: Optional[Dict[str, float]] = None):
        """Step all movements forward."""
        green_movements = set(self.phase_to_movements.get(active_phase, []))
        for m_id, m in self.movements.items():
            is_green = (m_id in green_movements)
            arr = arrivals.get(m_id) if arrivals else None
            m.step(dt=dt, is_green=is_green, external_arrivals=arr)

    def total_accumulated_delay(self) -> float:
        """Total accumulated vehicle delay across all movements via Trapezoidal integration."""
        return sum(m.get_accumulated_delay() * m.weight for m in self.movements.values())

    def current_total_queue(self) -> float:
        """Instantaneous queue sum across all approaches."""
        return sum(m.current_queue for m in self.movements.values())
