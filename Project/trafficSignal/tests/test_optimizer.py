"""Unit tests for constrained traffic signal optimization algorithms."""

import pytest
import numpy as np
from Traffic.config.settings import SignalTimingConfig
from Traffic.backend.optimizer import TrafficSignalOptimizer


def test_webster_split_equisaturation():
    """Verify Webster allocates green proportionally to flow ratios."""
    cfg = SignalTimingConfig(min_green=10.0, max_green=60.0, default_cycle_length=90.0)
    optimizer = TrafficSignalOptimizer(cfg)
    
    # NS approach has twice the volume of EW
    volumes = np.array([600.0, 300.0])
    sats = np.array([1800.0, 1800.0])
    
    splits = optimizer.calculate_webster_split(volumes, sats, cycle_length=90.0)
    
    total_effective = 90.0 - 2 * cfg.lost_time_per_phase  # 90 - 12 = 78s
    assert abs(np.sum(splits) - total_effective) < 1e-4
    # Phase 0 (NS) should receive more green than Phase 1 (EW)
    assert splits[0] > splits[1]
    assert np.all(splits >= cfg.min_green)
    assert np.all(splits <= cfg.max_green)


def test_slsqp_optimization_bounds():
    """Verify SLSQP outputs respect simplex sum and min/max green bounds."""
    cfg = SignalTimingConfig(min_green=12.0, max_green=50.0, default_cycle_length=80.0)
    optimizer = TrafficSignalOptimizer(cfg)
    
    queues = np.array([15.0, 5.0])
    arrivals = np.array([0.25, 0.10])
    sats = np.array([0.5, 0.5])
    
    res = optimizer.optimize_slsqp(queues, arrivals, sats, cycle_length=80.0)
    
    assert res.converged
    assert not res.is_fallback
    assert len(res.green_times) == 2
    assert np.all(res.green_times >= cfg.min_green - 1e-4)
    assert np.all(res.green_times <= cfg.max_green + 1e-4)
    
    eff_green = 80.0 - 2 * cfg.lost_time_per_phase
    assert abs(np.sum(res.green_times) - eff_green) < 1e-3


def test_optimizer_fallback_on_invalid_input():
    """Verify optimizer safely activates fallback when given degenerate values."""
    cfg = SignalTimingConfig()
    optimizer = TrafficSignalOptimizer(cfg)
    
    # Degenerate NaN inputs
    queues = np.array([np.nan, 5.0])
    arrivals = np.array([0.2, 0.1])
    sats = np.array([0.5, 0.5])
    
    res = optimizer.optimize_slsqp(queues, arrivals, sats)
    # Should catch gracefully and return a valid physical signal plan
    assert res.is_fallback or res.converged
    assert np.all(res.green_times >= cfg.min_green - 1e-4)
