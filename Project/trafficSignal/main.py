"""Main entrypoint for Adaptive Traffic Signal Optimization Simulator.

Usage:
    # Launch Desktop GUI Dashboard
    python main.py

    # Run Automated CLI Benchmark (A/B Test)
    python main.py --cli --duration 120 --demand Medium
"""

import sys
import argparse
from pathlib import Path

# Ensure Traffic package root is in python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR.parent))

from Traffic.config.settings import DemandProfile, find_sumo_binary, RESULTS_DIR
from Traffic.backend.paired_simulation import PairedSimulationRunner
from Traffic.backend.metrics import export_comparison_csv, export_comparison_json


def run_cli_benchmark(duration: int = 120, demand_name: str = "Medium", use_gui: bool = False, scenario_name: str = "balanced", seed: int = 42, site_id: str = "default_four_way"):
    """Run head-to-head comparison directly in terminal without desktop GUI."""
    print("=" * 70)
    print("  ADAPTIVE TRAFFIC SIGNAL OPTIMIZER - BENCHMARK RUNNER")
    print("=" * 70)
    
    sumo_bin = find_sumo_binary(gui=use_gui)
    print(f"SUMO Binary: {sumo_bin}")
    print(f"Simulation Duration: {duration} seconds | Seed: {seed} | Site: {site_id}")
    
    base_ns, base_ew = {
        "Low": (350, 250), "Medium": (600, 450), "Peak": (900, 700)
    }[demand_name]
    demand = DemandProfile(
        vehs_per_hour_ns=base_ns,
        vehs_per_hour_ew=base_ew,
        scenario=scenario_name,
        name=scenario_name.replace("_", " ").title(),
    )
    ns_factor = " × 2.4 scenario multiplier" if scenario_name == "heavy_ns" else ""
    print(f"Scenario: {demand.name} | NS={demand.vehs_per_hour_ns} veh/h/approach{ns_factor}, EW={demand.vehs_per_hour_ew} veh/h/approach\n")

    print(">>> Running fixed and adaptive control together on the same arrivals...")
    paired_runner = PairedSimulationRunner(use_gui=use_gui, duration=duration, seed=seed, demand=demand, site_id=site_id)
    base_summary, adapt_summary = paired_runner.run_sync()
    print("    Fixed-Time Baseline")
    print(f"    Completed Trips: {base_summary.total_completed_trips}")
    print(f"    Mean Waiting Time: {base_summary.mean_waiting_time:.2f} s")
    print(f"    Total Delay (Trapezoidal \u222b q dt): {base_summary.total_accumulated_delay:.1f} veh\u00b7s")
    print(f"    Mean Total Queue: {base_summary.mean_queue_length:.2f} veh")

    print("    Adaptive Optimization")
    print(f"    Completed Trips: {adapt_summary.total_completed_trips}")
    print(f"    Mean Waiting Time: {adapt_summary.mean_waiting_time:.2f} s")
    print(f"    Total Delay (Trapezoidal \u222b q dt): {adapt_summary.total_accumulated_delay:.1f} veh\u00b7s")
    print(f"    Mean Total Queue: {adapt_summary.mean_queue_length:.2f} veh")

    # 3. Export & Summary
    csv_file = export_comparison_csv(
        base_summary, adapt_summary,
        filename=f"comparison_{scenario_name}_{seed}_{duration}.csv"
    )
    json_file = export_comparison_json(
        base_summary,
        adapt_summary,
        metadata={
            "scenario": scenario_name,
            "seed": seed,
            "duration_sim_seconds": duration,
            "north_south_veh_per_hour_per_approach": demand.vehs_per_hour_ns,
            "east_west_veh_per_hour_per_approach": demand.vehs_per_hour_ew,
        },
        decisions=getattr(paired_runner.controller, "decision_log", []),
        filename=f"comparison_{scenario_name}_{seed}_{duration}.json",
    )
    
    def pct_change(b, a):
        return ((b - a) / b * 100.0) if b > 1e-4 else 0.0

    wait_reduction = pct_change(base_summary.mean_waiting_time, adapt_summary.mean_waiting_time)
    delay_reduction = pct_change(base_summary.total_accumulated_delay, adapt_summary.total_accumulated_delay)
    queue_reduction = pct_change(base_summary.mean_queue_length, adapt_summary.mean_queue_length)

    print("\n" + "=" * 70)
    print("  COMPARATIVE RESULTS SUMMARY")
    print("=" * 70)
    print(f"  Average Waiting Time:  {base_summary.mean_waiting_time:6.2f} s -> {adapt_summary.mean_waiting_time:6.2f} s  ({wait_reduction:+.1f}% change vs fixed)")
    print(f"  Total Vehicle Delay:   {base_summary.total_accumulated_delay:6.1f} s -> {adapt_summary.total_accumulated_delay:6.1f} s  ({delay_reduction:+.1f}% change vs fixed)")
    print(f"  Mean Queue Length:     {base_summary.mean_queue_length:6.2f} v -> {adapt_summary.mean_queue_length:6.2f} v  ({queue_reduction:+.1f}% change vs fixed)")
    print(f"  Completed Trips:       {base_summary.total_completed_trips:6d}   -> {adapt_summary.total_completed_trips:6d}")
    print(f"  Results saved to:      {csv_file.resolve()}")
    print(f"  JSON record saved to:  {json_file.resolve()}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Adaptive Traffic Signal Optimization Simulator")
    parser.add_argument("--cli", action="store_true", help="Run benchmark in CLI mode without launching GUI")
    parser.add_argument("--duration", type=int, default=120, help="Simulation duration in seconds (default: 120)")
    parser.add_argument("--demand", type=str, choices=["Low", "Medium", "Peak"], default="Medium", help="Demand preset")
    parser.add_argument("--scenario", choices=["balanced", "heavy_ns", "sudden_surge", "rush_hour"], default="balanced", help="Seeded arrival pattern")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible demand")
    parser.add_argument("--site", type=str, default="default_four_way", choices=["default_four_way", "boring_road_patna"], help="Site scenario")
    parser.add_argument("--gui", action="store_true", help="Launch SUMO-GUI animation window")
    
    args = parser.parse_args()

    if args.cli:
        run_cli_benchmark(duration=args.duration, demand_name=args.demand, use_gui=args.gui, scenario_name=args.scenario, seed=args.seed, site_id=args.site)
    else:
        from Traffic.frontend.app import launch_app
        launch_app()


if __name__ == "__main__":
    main()
