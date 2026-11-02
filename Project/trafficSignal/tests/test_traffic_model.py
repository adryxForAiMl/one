"""Unit tests for discrete-time queue evolution model."""

import pytest
import numpy as np
from Traffic.backend.traffic_model import MovementState, IntersectionQueueModel


def test_movement_queue_conservation_and_green():
    """Verify queue accumulates during red and discharges during green."""
    m = MovementState(
        movement_id="North",
        name="North Approach",
        saturation_flow=0.5,  # 0.5 veh/s capacity
        arrival_rate=0.2,     # 0.2 veh/s arrival
        capacity=30
    )
    
    # 10 seconds of RED: 0.2 * 10 = 2.0 arrivals, 0 departures
    for _ in range(10):
        arr, dep = m.step(dt=1.0, is_green=False)
        assert dep == 0.0
        assert arr == 0.2
        
    assert abs(m.current_queue - 2.0) < 1e-5
    
    # 5 seconds of GREEN: arrivals = 0.2/s, max dep = 0.5/s
    # Net change per second = 0.2 - 0.5 = -0.3
    # After 5 seconds: queue = max(0, 2.0 - 1.5) = 0.5
    for _ in range(5):
        m.step(dt=1.0, is_green=True)
        
    assert abs(m.current_queue - 0.5) < 1e-5


def test_movement_non_negativity_and_spillback():
    """Verify queue cannot drop below 0 or exceed storage capacity."""
    m = MovementState(
        movement_id="East",
        name="East Approach",
        saturation_flow=1.0,
        arrival_rate=0.0,
        capacity=20
    )
    m.current_queue = 1.0
    
    # Green step with 0 arrivals and 1.0 departure capacity
    m.step(dt=1.0, is_green=True)
    assert m.current_queue == 0.0
    
    # Another green step should remain 0.0, not negative
    m.step(dt=1.0, is_green=True)
    assert m.current_queue == 0.0
    
    # Massive arrival surge: should cap at capacity (20)
    m.step(dt=1.0, is_green=False, external_arrivals=50.0)
    assert m.current_queue == 20.0


def test_intersection_accumulated_delay():
    """Verify total intersection delay aggregates across approaches."""
    intersection = IntersectionQueueModel(["North", "South", "East", "West"])
    intersection.reset()
    
    # 10 steps on Phase 0 (North-South Green, East-West Red)
    for _ in range(10):
        intersection.step(dt=1.0, active_phase=0)
        
    delay = intersection.total_accumulated_delay()
    assert delay > 0.0
    assert intersection.current_total_queue() >= 0.0
