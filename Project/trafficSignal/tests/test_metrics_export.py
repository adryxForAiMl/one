import csv

from Traffic.backend import metrics
from Traffic.backend.metrics import SimulationSummary, export_comparison_csv, export_comparison_json


def summary(mode, wait, delay, queue, trips):
    return SimulationSummary(
        mode=mode, duration=120, total_completed_trips=trips,
        mean_queue_length=queue, peak_95th_queue_length=queue,
        mean_waiting_time=wait, peak_waiting_time=wait,
        total_accumulated_delay=delay, mean_speed_kmh=30,
        numerical_integration_error=0,
    )


def test_comparison_export_keeps_negative_changes_truthful(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "RESULTS_DIR", tmp_path)
    path = export_comparison_csv(
        summary("Fixed", wait=2, delay=100, queue=4, trips=20),
        summary("Adaptive", wait=3, delay=120, queue=5, trips=18),
        filename="comparison.csv",
    )
    with path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["Change vs Fixed (%)"] == "-50.0%"
    assert rows[1]["Change vs Fixed (%)"] == "-20.0%"
    assert rows[4]["Change vs Fixed (%)"] == "-10.0%"


def test_comparison_json_includes_settings_summaries_deltas_and_decisions(tmp_path, monkeypatch):
    monkeypatch.setattr(metrics, "RESULTS_DIR", tmp_path)
    path = export_comparison_json(
        summary("Fixed", wait=2, delay=100, queue=4, trips=20),
        summary("Adaptive", wait=3, delay=120, queue=5, trips=18),
        metadata={"scenario": "balanced", "seed": 1},
        decisions=[{"reason": "measured queue"}],
        filename="comparison.json",
    )
    import json
    result = json.loads(path.read_text())
    assert result["metadata"] == {"scenario": "balanced", "seed": 1}
    assert result["change_vs_fixed_percent"]["mean_wait_reduction"] == -50.0
    assert result["adaptive_decisions"][0]["reason"] == "measured queue"
