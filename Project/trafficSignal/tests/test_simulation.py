"""Integration tests for SUMO network generation and TraCI simulation execution."""

import pytest
from pathlib import Path
from types import SimpleNamespace
from Traffic.config.settings import NETWORKS_DIR, DemandProfile, find_sumo_binary
from Traffic.backend.data_loader import SumoNetworkBuilder
from Traffic.backend.simulation import SimulationRunner
from Traffic.backend.paired_simulation import PairedSimulationRunner
from Traffic.backend import simulation


def test_scenario_generation():
    """Verify all SUMO XML artifacts are created and non-empty."""
    builder = SumoNetworkBuilder()
    demand = DemandProfile(vehs_per_hour_ns=500, vehs_per_hour_ew=350)
    cfg_path = builder.generate_full_scenario(demand=demand, duration=60, seed=42)
    
    assert cfg_path.exists()
    assert (NETWORKS_DIR / "intersection.net.xml").exists()
    assert (NETWORKS_DIR / "intersection.rou.xml").exists()
    assert (NETWORKS_DIR / "intersection.det.xml").exists()
    assert (NETWORKS_DIR / "simulation.sumocfg").exists()
    assert (NETWORKS_DIR / "intersection.net.xml").stat().st_size > 1000
    import xml.etree.ElementTree as ET
    location = ET.parse(NETWORKS_DIR / "intersection.net.xml").getroot().find("location")
    assert location is not None
    assert location.attrib["netOffset"] == "0.00,0.00"


def test_route_generation_is_seed_deterministic(tmp_path):
    builder = SumoNetworkBuilder(output_dir=tmp_path)
    demand = DemandProfile(vehs_per_hour_ns=500, vehs_per_hour_ew=350)
    first = builder._write_routes_file(demand, duration=60, seed=21).read_text()
    repeated = builder._write_routes_file(demand, duration=60, seed=21).read_text()
    other = builder._write_routes_file(demand, duration=60, seed=22).read_text()
    assert first == repeated
    assert first != other


def test_routes_include_six_reproducible_vehicle_classes(tmp_path):
    import xml.etree.ElementTree as ET

    builder = SumoNetworkBuilder(output_dir=tmp_path)
    route_file = builder._write_routes_file(DemandProfile(vehs_per_hour_ns=3600, vehs_per_hour_ew=3600), 600, 42)
    root = ET.parse(route_file).getroot()
    vehicle_types = {item.attrib["id"] for item in root.findall("vType")}
    assigned_types = {item.attrib["type"] for item in root.findall("vehicle")}
    assert vehicle_types == {"hatchback", "sedan", "suv", "van", "bus", "truck"}
    assert assigned_types == vehicle_types


def test_sudden_surge_increases_later_poisson_arrivals(tmp_path):
    import xml.etree.ElementTree as ET

    builder = SumoNetworkBuilder(output_dir=tmp_path)
    demand = DemandProfile(vehs_per_hour_ns=1800, vehs_per_hour_ew=1800, scenario="sudden_surge")
    route_file = builder._write_routes_file(demand, duration=300, seed=15)
    vehicles = ET.parse(route_file).findall("vehicle")
    first_half = sum(float(v.attrib["depart"]) < 150 for v in vehicles)
    second_half = sum(float(v.attrib["depart"]) >= 150 for v in vehicles)
    assert second_half > first_half


def test_heavy_ns_scenario_increases_ns_arrivals(tmp_path):
    import xml.etree.ElementTree as ET

    builder = SumoNetworkBuilder(output_dir=tmp_path)
    demand = DemandProfile(vehs_per_hour_ns=600, vehs_per_hour_ew=600, scenario="heavy_ns")
    route_file = builder._write_routes_file(demand, duration=360, seed=8)
    vehicles = ET.parse(route_file).findall("vehicle")
    ns = sum(ET.parse(route_file).find(f".//route[@id='{vehicle.attrib['route']}']").attrib["edges"].startswith(("edge_N_in", "edge_S_in")) for vehicle in vehicles)
    ew = len(vehicles) - ns
    assert ns > ew


def test_async_runner_reports_connection_failure(monkeypatch):
    runner = SimulationRunner(mode="Fixed_Baseline", duration=1)
    monkeypatch.setattr(runner, "run_sync", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("SUMO unavailable")))
    errors = []
    runner.run_async(error_callback=errors.append)
    runner._thread.join(timeout=2)
    assert len(errors) == 1
    assert "SUMO unavailable" in str(errors[0])


def test_runner_calculates_mean_completed_trip_travel_time(monkeypatch):
    runner = SimulationRunner(mode="Fixed_Baseline", duration=10)
    state = {"time": 2.0, "departed": ["veh-1"], "arrived": [], "active": ["veh-1"]}
    fake_simulation = SimpleNamespace(
        getTime=lambda: state["time"],
        getDepartedIDList=lambda: state["departed"],
        getArrivedIDList=lambda: state["arrived"],
    )
    fake_vehicle = SimpleNamespace(
        getIDList=lambda: state["active"],
        getWaitingTime=lambda _vehicle_id: 0.0,
        getSpeed=lambda _vehicle_id: 5.0,
        getPosition=lambda _vehicle_id: (0.0, 0.0),
        getAngle=lambda _vehicle_id: 0.0,
        getLaneID=lambda _vehicle_id: "lane-1",
        getTypeID=lambda _vehicle_id: "sedan",
    )
    monkeypatch.setattr(simulation.traci, "simulation", fake_simulation)
    monkeypatch.setattr(simulation.traci, "vehicle", fake_vehicle)

    runner._sample_network_metrics()
    state.update(time=9.0, departed=[], arrived=["veh-1"], active=[])
    runner._sample_network_metrics()

    assert runner.average_completed_trip_travel_time == 7.0


def test_paired_runner_steps_same_seed_in_lockstep():
    runner = PairedSimulationRunner(duration=15, seed=101, demand=DemandProfile())
    fixed, adaptive = runner.run_sync()
    fixed_df = runner.fixed_runner.metrics.get_dataframe()
    adaptive_df = runner.adaptive_runner.metrics.get_dataframe()
    assert fixed.duration >= 14
    assert adaptive.duration >= 14
    assert fixed_df["time"].tolist() == adaptive_df["time"].tolist()
    assert fixed_df["active_vehicles"].tolist() == adaptive_df["active_vehicles"].tolist()
    assert fixed_df["total_queue"].tolist() == adaptive_df["total_queue"].tolist()


def test_short_simulation_headless_fixed():
    """Run a 15-second headless simulation with fixed controller and check telemetry."""
    runner = SimulationRunner(
        mode="Fixed_Baseline",
        use_gui=False,
        duration=15,
        seed=101
    )
    summary = runner.run_sync()
    
    assert summary.duration >= 14.0
    assert len(runner.metrics.history) == 15
    # Verify non-negative metrics
    assert summary.mean_queue_length >= 0.0
    assert summary.total_accumulated_delay >= 0.0


def test_short_simulation_headless_adaptive():
    """Run a 15-second headless simulation with adaptive controller."""
    runner = SimulationRunner(
        mode="Adaptive_Optimized",
        use_gui=False,
        duration=15,
        seed=101
    )
    summary = runner.run_sync()
    
    assert summary.duration >= 14.0
    assert len(runner.metrics.history) == 15
    assert summary.mean_waiting_time >= 0.0
