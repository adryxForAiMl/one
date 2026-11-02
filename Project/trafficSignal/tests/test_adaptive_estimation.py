import pytest

from Traffic.backend.simulation import AdaptiveController
from Traffic.config.settings import DemandProfile


def test_detector_flow_estimate_uses_unique_solution():
    controller = AdaptiveController(demand=DemandProfile(vehs_per_hour_ns=600, vehs_per_hour_ew=450))
    controller.record_detector_counts({"North": 3, "South": 2, "East": 1, "West": 2}, dt=10)
    rates, source, status = controller._estimate_phase_arrival_rates()
    assert rates == pytest.approx([0.5, 0.3])
    assert source == "Gauss-Jordan detector estimate"
    assert status == "unique"
    assert controller.last_flow_estimation["detector_counts"] == {"North": 3, "South": 2, "East": 1, "West": 2}
    assert controller.last_flow_estimation["detector_rates"] == pytest.approx({"North": 0.3, "South": 0.2, "East": 0.1, "West": 0.2})
    assert controller.last_flow_estimation["interval_seconds"] == 10
    assert controller.detector_elapsed == 0


def test_detector_flow_estimate_falls_back_when_implausible():
    controller = AdaptiveController()
    controller.record_detector_counts({"North": 20, "South": 20, "East": 0, "West": 0}, dt=1)
    rates, source, status = controller._estimate_phase_arrival_rates()
    assert rates == pytest.approx([1.2, 0.0])
    assert source == "measured detector fallback"
    assert status == "unique"


def test_detector_flow_uses_configured_demand_before_first_sample():
    controller = AdaptiveController(demand=DemandProfile(vehs_per_hour_ns=720, vehs_per_hour_ew=360))
    rates, source, status = controller._estimate_phase_arrival_rates()
    assert rates == pytest.approx([0.4, 0.2])
    assert source == "configured demand"
    assert status == "no detector interval yet"
