"""Traffic performance metrics collection, numerical accumulation, and CSV export.

Tracks:
- Queue length per lane and approach
- Accumulated waiting time via Composite Trapezoidal Rule
- Travel time and vehicle speed
- Total throughput (completed trips)
- Comparison delta calculations between Fixed-Time baseline and Adaptive control
"""

from __future__ import annotations
import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

from Traffic.backend.numerical_methods import trapezoidal_rule, trapezoidal_cumulative
from Traffic.config.settings import RESULTS_DIR


@dataclass
class StepTelemetry:
    """Telemetry recorded at a single discrete simulation step."""
    time: float
    mode: str                     # 'Fixed_Baseline' or 'Adaptive_Optimized'
    active_vehicles: int
    completed_vehicles: int
    total_queue: float
    queue_north: float
    queue_south: float
    queue_east: float
    queue_west: float
    avg_waiting_time: float       # Current mean vehicle waiting time (s)
    accumulated_delay: float      # Integrated vehicle-seconds via Trapezoidal rule
    avg_speed: float              # Mean network speed (m/s)
    current_phase: int
    phase_green_time: float


@dataclass
class SimulationSummary:
    """End-of-run statistical evaluation for comparative benchmarking."""
    mode: str
    duration: float
    total_completed_trips: int
    mean_queue_length: float
    peak_95th_queue_length: float
    mean_waiting_time: float
    peak_waiting_time: float
    total_accumulated_delay: float  # Trapezoidal integral \int q(t) dt
    mean_speed_kmh: float
    numerical_integration_error: float


class MetricsCollector:
    """Manages telemetry recording and metrics aggregation during simulation."""

    def __init__(self, mode: str = "Fixed_Baseline"):
        self.mode = mode
        self.history: List[StepTelemetry] = []
        self._completed_trips_count: int = 0

    def reset(self, mode: Optional[str] = None):
        """Reset internal metrics buffers."""
        if mode:
            self.mode = mode
        self.history.clear()
        self._completed_trips_count = 0

    def record_step(
        self,
        time: float,
        active_vehicles: int,
        completed_delta: int,
        queues: Dict[str, float],
        waiting_time: float,
        avg_speed: float,
        current_phase: int,
        phase_green: float
    ) -> StepTelemetry:
        """Log a single simulation time step."""
        self._completed_trips_count += completed_delta
        
        q_n = queues.get("North", 0.0)
        q_s = queues.get("South", 0.0)
        q_e = queues.get("East", 0.0)
        q_w = queues.get("West", 0.0)
        total_q = q_n + q_s + q_e + q_w
        
        # Calculate running trapezoidal delay
        if len(self.history) == 0:
            accum_delay = 0.0
        else:
            prev = self.history[-1]
            dt = time - prev.time
            segment = 0.5 * (prev.total_queue + total_q) * dt
            accum_delay = prev.accumulated_delay + segment
            
        record = StepTelemetry(
            time=time,
            mode=self.mode,
            active_vehicles=active_vehicles,
            completed_vehicles=self._completed_trips_count,
            total_queue=total_q,
            queue_north=q_n,
            queue_south=q_s,
            queue_east=q_e,
            queue_west=q_w,
            avg_waiting_time=waiting_time,
            accumulated_delay=accum_delay,
            avg_speed=avg_speed,
            current_phase=current_phase,
            phase_green_time=phase_green
        )
        self.history.append(record)
        return record

    def get_dataframe(self) -> pd.DataFrame:
        """Convert recorded history to a Pandas DataFrame."""
        if not self.history:
            return pd.DataFrame()
        return pd.DataFrame([asdict(h) for h in self.history])

    def compute_summary(self) -> SimulationSummary:
        """Compute aggregate summary metrics."""
        df = self.get_dataframe()
        if df.empty:
            return SimulationSummary(
                mode=self.mode, duration=0.0, total_completed_trips=0,
                mean_queue_length=0.0, peak_95th_queue_length=0.0,
                mean_waiting_time=0.0, peak_waiting_time=0.0,
                total_accumulated_delay=0.0, mean_speed_kmh=0.0,
                numerical_integration_error=0.0
            )

        duration = float(df['time'].iloc[-1] - df['time'].iloc[0])
        total_trips = int(df['completed_vehicles'].iloc[-1])
        mean_q = float(df['total_queue'].mean())
        p95_q = float(np.percentile(df['total_queue'], 95))
        peak_wait = float(df['avg_waiting_time'].max())

        # Vehicle-count-weighted mean waiting time: ∫(wait × n_active)dt / ∫n_active dt
        # This correctly accounts for completed trips leaving the sample population.
        times = df['time'].values
        w_vals = df['avg_waiting_time'].values
        n_vals = df['active_vehicles'].values.astype(float)
        weighted_wait_integral = trapezoidal_rule(w_vals * n_vals, times)
        vehicle_time_integral = trapezoidal_rule(n_vals, times)
        mean_wait = float(weighted_wait_integral / vehicle_time_integral) if vehicle_time_integral > 1e-6 else 0.0

        # Trapezoidal integral of queue over time (vehicle-seconds of delay)
        total_delay = trapezoidal_rule(df['total_queue'].values, times)

        # Trapezoidal error estimate via 2-step coarse grid comparison (Richardson)
        if len(df) > 4:
            coarse_y = df['total_queue'].values[::2]
            coarse_x = times[::2]
            coarse_delay = trapezoidal_rule(coarse_y, coarse_x)
            trunc_error = abs(total_delay - coarse_delay) / 3.0
        else:
            trunc_error = 0.0

        mean_speed = float(df['avg_speed'].mean() * 3.6)  # m/s to km/h

        return SimulationSummary(
            mode=self.mode,
            duration=duration,
            total_completed_trips=total_trips,
            mean_queue_length=mean_q,
            peak_95th_queue_length=p95_q,
            mean_waiting_time=mean_wait,
            peak_waiting_time=peak_wait,
            total_accumulated_delay=total_delay,
            mean_speed_kmh=mean_speed,
            numerical_integration_error=trunc_error
        )

    def export_csv(self, filename: Optional[str] = None) -> Path:
        """Export time-series telemetry to CSV file."""
        df = self.get_dataframe()
        if filename is None:
            safe_mode = self.mode.lower().replace(" ", "_")
            filename = f"telemetry_{safe_mode}.csv"
            
        export_path = RESULTS_DIR / filename
        df.to_csv(export_path, index=False)
        return export_path


def export_comparison_csv(
    baseline_summary: SimulationSummary,
    adaptive_summary: SimulationSummary,
    filename: str = "comparison_benchmark.csv"
) -> Path:
    """Save direct A/B metrics and percentage changes (negative means worse) to CSV."""
    def calc_reduction(base: float, adapt: float) -> float:
        if base > 1e-6:
            return float(((base - adapt) / base) * 100.0)
        return 0.0

    comparison_data = [
        {
            "Metric": "Average Waiting Time (s)",
            "Baseline (Fixed)": f"{baseline_summary.mean_waiting_time:.2f}",
            "Proposed (Adaptive)": f"{adaptive_summary.mean_waiting_time:.2f}",
            "Change vs Fixed (%)": f"{calc_reduction(baseline_summary.mean_waiting_time, adaptive_summary.mean_waiting_time):.1f}%"
        },
        {
            "Metric": "Total Accumulated Delay (veh-s)",
            "Baseline (Fixed)": f"{baseline_summary.total_accumulated_delay:.1f}",
            "Proposed (Adaptive)": f"{adaptive_summary.total_accumulated_delay:.1f}",
            "Change vs Fixed (%)": f"{calc_reduction(baseline_summary.total_accumulated_delay, adaptive_summary.total_accumulated_delay):.1f}%"
        },
        {
            "Metric": "Mean Total Queue (veh)",
            "Baseline (Fixed)": f"{baseline_summary.mean_queue_length:.2f}",
            "Proposed (Adaptive)": f"{adaptive_summary.mean_queue_length:.2f}",
            "Change vs Fixed (%)": f"{calc_reduction(baseline_summary.mean_queue_length, adaptive_summary.mean_queue_length):.1f}%"
        },
        {
            "Metric": "95th Percentile Peak Queue (veh)",
            "Baseline (Fixed)": f"{baseline_summary.peak_95th_queue_length:.2f}",
            "Proposed (Adaptive)": f"{adaptive_summary.peak_95th_queue_length:.2f}",
            "Change vs Fixed (%)": f"{calc_reduction(baseline_summary.peak_95th_queue_length, adaptive_summary.peak_95th_queue_length):.1f}%"
        },
        {
            "Metric": "Total Throughput (Completed Trips)",
            "Baseline (Fixed)": f"{baseline_summary.total_completed_trips}",
            "Proposed (Adaptive)": f"{adaptive_summary.total_completed_trips}",
            "Change vs Fixed (%)": f"{((adaptive_summary.total_completed_trips - baseline_summary.total_completed_trips) / max(1, baseline_summary.total_completed_trips)) * 100.0:.1f}%"
        },
        {
            "Metric": "Average Network Speed (km/h)",
            "Baseline (Fixed)": f"{baseline_summary.mean_speed_kmh:.2f}",
            "Proposed (Adaptive)": f"{adaptive_summary.mean_speed_kmh:.2f}",
            "Change vs Fixed (%)": f"{((adaptive_summary.mean_speed_kmh - baseline_summary.mean_speed_kmh) / max(0.1, baseline_summary.mean_speed_kmh)) * 100.0:.1f}%"
        },
        {
            "Metric": "Trapezoidal Numerical Truncation Error (s)",
            "Baseline (Fixed)": f"{baseline_summary.numerical_integration_error:.4f}",
            "Proposed (Adaptive)": f"{adaptive_summary.numerical_integration_error:.4f}",
            "Change vs Fixed (%)": "N/A"
        }
    ]

    out_file = RESULTS_DIR / filename
    with open(out_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Metric", "Baseline (Fixed)", "Proposed (Adaptive)", "Change vs Fixed (%)"])
        writer.writeheader()
        writer.writerows(comparison_data)

    return out_file


def export_comparison_json(
    baseline_summary: SimulationSummary,
    adaptive_summary: SimulationSummary,
    *,
    metadata: Dict[str, Any],
    decisions: Optional[List[Dict[str, Any]]] = None,
    filename: str = "comparison.json",
) -> Path:
    """Export reproducibility settings, measured summaries, deltas, and decisions."""
    def reduction(base: float, adaptive: float) -> Optional[float]:
        return ((base - adaptive) / base * 100.0) if base > 1e-9 else None

    result = {
        "metadata": metadata,
        "fixed": asdict(baseline_summary),
        "adaptive": asdict(adaptive_summary),
        "change_vs_fixed_percent": {
            "mean_wait_reduction": reduction(baseline_summary.mean_waiting_time, adaptive_summary.mean_waiting_time),
            "delay_reduction": reduction(baseline_summary.total_accumulated_delay, adaptive_summary.total_accumulated_delay),
            "mean_queue_reduction": reduction(baseline_summary.mean_queue_length, adaptive_summary.mean_queue_length),
            "completed_trips_change": (
                (adaptive_summary.total_completed_trips - baseline_summary.total_completed_trips)
                / baseline_summary.total_completed_trips * 100.0
                if baseline_summary.total_completed_trips else None
            ),
        },
        "adaptive_decisions": decisions or [],
    }
    out_file = RESULTS_DIR / filename
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return out_file
