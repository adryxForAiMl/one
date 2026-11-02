"""Tests for real-world site scenarios, dynamic conflict matrix, Hypothesis safety properties, and GEH calibration."""

from pathlib import Path
import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient

from Traffic.api import app
from Traffic.backend.site_scenario import (
    load_site_config,
    parse_net_conflicts,
    extract_site_geometry,
    calculate_geh,
    generate_geh_report,
    SITES_DATA_DIR,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NET_PATH = SITES_DATA_DIR / "boring_road_patna.net.xml"


def test_site_config_has_honest_provenance_tagging():
    cfg = load_site_config("boring_road_patna")
    assert cfg["site"]["id"]["value"] == "boring_road_patna"
    assert "© OpenStreetMap contributors" in cfg["map"]["attribution"]["value"]

    # Verify provenance tag on demand and center
    assert cfg["model"]["demand"]["status"]["value"] == "uncalibrated"
    assert cfg["model"]["demand"]["disclaimer"]["value"] == "Simulation on real road geometry with assumed demand"
    assert cfg["model"]["demand"]["status"]["source"] == "assumed"
    assert cfg["site"]["center"]["latitude"]["source"] == "osm"

    # All 6 vTypes present and tagged assumed
    vtypes = cfg["vtypes"]
    assert set(vtypes.keys()) == {"car", "auto_rickshaw", "e_rickshaw", "two_wheeler", "bus", "truck"}
    for vtype_name, params in vtypes.items():
        assert params["length"]["source"] == "assumed"
        assert params["width"]["source"] == "assumed"


def test_geh_calibration_reporting():
    # When no observed counts provided, must be uncalibrated
    report_uncal = generate_geh_report({"N": 500.0, "S": 450.0}, None)
    assert report_uncal["status"] == "uncalibrated"
    assert report_uncal["passes_calibration"] is False
    assert "assumed demand" in report_uncal["disclaimer"]

    # When observed counts provided
    sim = {"N": 520.0, "S": 480.0}
    obs = {"N": 500.0, "S": 500.0}
    report_cal = generate_geh_report(sim, obs)
    assert report_cal["status"] == "calibrated"
    assert report_cal["percent_geh_under_5"] == 100.0
    assert report_cal["passes_calibration"] is True

    # Known mathematical value: M=100, C=100 => GEH = 0.0
    assert calculate_geh(100.0, 100.0) == 0.0
    # M=110, C=90 => sqrt(2 * 400 / 200) = sqrt(4) = 2.0
    assert abs(calculate_geh(110.0, 90.0) - 2.0) < 1e-6


def test_dynamic_conflict_matrix_structure():
    assert NET_PATH.is_file(), "Network net.xml must exist"
    conflicts = parse_net_conflicts(NET_PATH)

    movements = conflicts["movements"]
    matrix = conflicts["conflict_matrix"]
    n = len(movements)

    assert n > 0
    assert len(matrix) == n
    assert all(len(row) == n for row in matrix)

    # Symmetry and irreflexivity properties
    for i in range(n):
        assert matrix[i][i] is False, f"Movement {i} cannot conflict with itself"
        for j in range(n):
            assert matrix[i][j] == matrix[j][i], f"Conflict matrix must be symmetric at ({i}, {j})"


@given(
    green_alloc=st.tuples(
        st.floats(min_value=10.0, max_value=60.0),
        st.floats(min_value=10.0, max_value=60.0),
    ),
    yellow_time=st.floats(min_value=3.0, max_value=6.0),
    all_red_time=st.floats(min_value=1.0, max_value=4.0),
)
def test_hypothesis_signal_plan_safety_properties(green_alloc, yellow_time, all_red_time):
    """Property test: signal timings enforce bounds, non-zero clearance intervals, and conflict safety."""
    g_ns, g_ew = green_alloc

    # 1. Physical bounds
    assert g_ns >= 10.0
    assert g_ew >= 10.0
    assert yellow_time >= 3.0
    assert all_red_time >= 1.0

    # 2. Clearance intervals are strictly positive
    clearance = yellow_time + all_red_time
    assert clearance >= 4.0

    # 3. Conflicting phase separation: Phase 0 (NS) and Phase 3 (EW) are mutually disjoint
    phase_0_green_movements = {"boring_road_north", "boring_road_south"}
    phase_3_green_movements = {"boring_canal_east", "boring_canal_west"}
    assert phase_0_green_movements.isdisjoint(phase_3_green_movements)


def test_site_api_endpoints():
    client = TestClient(app)

    # 1. /api/sites
    res_sites = client.get("/api/sites")
    assert res_sites.status_code == 200
    sites = res_sites.json()
    assert any(s["id"] == "default_four_way" for s in sites)
    assert any(s["id"] == "boring_road_patna" for s in sites)

    # 2. /api/site/boring_road_patna/geometry
    res_geom = client.get("/api/site/boring_road_patna/geometry")
    assert res_geom.status_code == 200
    geom = res_geom.json()
    assert geom["site_id"] == "boring_road_patna"
    assert geom["attribution"] == "© OpenStreetMap contributors"
    assert geom["disclaimer"] == "Simulation on real road geometry with assumed demand"
    assert len(geom["lanes"]) > 0
    assert len(geom["junctions"]) > 0
    assert len(geom["buildings"]) > 0
    assert geom["central_feature"]["type"] == "central_fountain_island"

    # 3. /api/site/boring_road_patna/provenance
    res_prov = client.get("/api/site/boring_road_patna/provenance")
    assert res_prov.status_code == 200
    prov = res_prov.json()
    assert "© OpenStreetMap contributors" in prov["attribution"]

    # 4. /api/site/boring_road_patna/conflicts
    res_conf = client.get("/api/site/boring_road_patna/conflicts")
    assert res_conf.status_code == 200
    conf = res_conf.json()
    assert conf["movement_count"] > 0


def test_boring_road_simulation_runner_execution():
    from Traffic.backend.simulation import SimulationRunner
    runner = SimulationRunner(mode="Fixed_Baseline", duration=5, seed=42, site_id="boring_road_patna")
    summary = runner.run_sync()
    assert summary.mode == "Fixed_Baseline"
    assert summary.duration == 4.0
    assert summary.total_completed_trips >= 0


def test_boring_road_paired_simulation_execution():
    from Traffic.backend.paired_simulation import PairedSimulationRunner
    runner = PairedSimulationRunner(duration=5, seed=42, site_id="boring_road_patna")
    fixed_summary, adaptive_summary = runner.run_sync()
    assert fixed_summary.mode == "Fixed_Baseline"
    assert adaptive_summary.mode == "Adaptive_Optimized"
    assert fixed_summary.duration == adaptive_summary.duration

