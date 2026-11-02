"""Main CustomTkinter desktop application window.

Connects:
- DashboardControls
- MetricCards (KPI overview)
- TrafficChartsPanel (embedded Matplotlib)
- TraCI SimulationRunner (Fixed vs Adaptive vs Benchmark)
- Real-time thread-safe UI telemetry updates
"""

from __future__ import annotations
import os
import sys
import threading
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import customtkinter as ctk
from Traffic.config.tokens import COLORS

# Keep Matplotlib's font/config cache in a writable per-user temp location.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "traffic-matplotlib"))

from Traffic.config.settings import DemandProfile, SignalTimingConfig, RESULTS_DIR
from Traffic.backend.simulation import SimulationRunner
from Traffic.backend.paired_simulation import PairedSimulationRunner
from Traffic.backend.metrics import StepTelemetry, SimulationSummary, export_comparison_csv, export_comparison_json
from Traffic.frontend.dashboard import MetricCard, DashboardControls
from Traffic.frontend.charts import TrafficChartsPanel


class TrafficOptimizerApp(ctk.CTk):
    """Main Desktop Application Window."""

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("Adaptive Traffic Signal Optimization Simulator | B.Tech Project")
        self.geometry("1280x840")
        self.minsize(1080, 720)
        self.configure(fg_color=COLORS["page"])

        self.current_runner: Optional[SimulationRunner] = None
        self.baseline_summary: Optional[SimulationSummary] = None
        self.adaptive_summary: Optional[SimulationSummary] = None
        self.baseline_df: pd.DataFrame = pd.DataFrame()
        self.adaptive_df: pd.DataFrame = pd.DataFrame()
        self._stop_benchmark = False
        self._benchmark_thread: Optional[threading.Thread] = None

        self._build_header()
        self._build_kpi_cards()
        self._build_main_layout()
        self.bind("<space>", self._toggle_pause)
        self.bind("<KeyPress-r>", self._reset_shortcut)
        self.bind("<KeyPress-R>", self._reset_shortcut)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["surface"], height=60, corner_radius=0)
        header.pack(fill="x", side="top")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        lbl_main = ctk.CTkLabel(
            title_box,
            text="ADAPTIVE TRAFFIC SIGNAL OPTIMIZER",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["navy"]
        )
        lbl_main.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="Numerical Methods (Trapezoidal Integration, OLS Saturation Estimation & Constrained SLSQP/PGD)",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["muted"]
        )
        lbl_sub.pack(anchor="w")

        self.lbl_badge = ctk.CTkLabel(
            header,
            text="SYSTEM READY",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLORS["border"],
            text_color=COLORS["green"],
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.lbl_badge.pack(side="right", padx=20, pady=16)

    def _build_kpi_cards(self):
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=18, pady=(12, 6))

        self.card_time = MetricCard(cards_frame, title="SIMULATION TIME", initial_value="0.0", unit="seconds", accent_color=COLORS["primary"])
        self.card_time.pack(side="left", fill="both", expand=True, padx=4)

        self.card_active = MetricCard(cards_frame, title="ACTIVE VEHICLES", initial_value="0", unit="in network", accent_color=COLORS["amber"])
        self.card_active.pack(side="left", fill="both", expand=True, padx=4)

        self.card_wait = MetricCard(cards_frame, title="MEAN WAITING TIME", initial_value="0.0", unit="seconds/veh", accent_color=COLORS["amber"])
        self.card_wait.pack(side="left", fill="both", expand=True, padx=4)

        self.card_queue = MetricCard(cards_frame, title="TOTAL QUEUE", initial_value="0.0", unit="halting vehicles", accent_color=COLORS["red"])
        self.card_queue.pack(side="left", fill="both", expand=True, padx=4)

        self.card_reduction = MetricCard(cards_frame, title="WAIT REDUCTION", initial_value="--", unit="% vs fixed", accent_color=COLORS["green"])
        self.card_reduction.pack(side="left", fill="both", expand=True, padx=4)

    def _build_main_layout(self):
        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=18, pady=(6, 12))

        # Left: Controls
        self.controls = DashboardControls(
            body_frame,
            on_start=self.handle_start,
            on_pause=self.handle_pause,
            on_resume=self.handle_resume,
            on_stop=self.handle_stop,
            on_reset=self.handle_reset,
            on_export=self.handle_export
        )
        self.controls.pack(side="left", fill="y", padx=(0, 10))

        # Right: Matplotlib Charts Panel
        right_panel = ctk.CTkFrame(body_frame, fg_color=COLORS["surface"], corner_radius=12)
        right_panel.pack(side="right", fill="both", expand=True)

        self.charts = TrafficChartsPanel(right_panel)

    def handle_start(self):
        """Initiate simulation according to configured mode."""
        if self.current_runner and self.current_runner.is_running:
            self.controls.log_message("A simulation is already running.")
            return
        self._stop_benchmark = False
        settings = self.controls.get_settings()
        mode = settings["mode"]
        
        self.charts.reset()
        self.card_reduction.update_value("--")
        self.controls.log_message(f"Preparing run: Mode={mode}, Duration={settings['duration']}s, GUI={settings['use_gui']}")
        self.lbl_badge.configure(text="RUNNING SIMULATION", text_color=COLORS["amber"])

        demand = DemandProfile(
            vehs_per_hour_ns=settings["vol_ns"],
            vehs_per_hour_ew=settings["vol_ew"],
            scenario=settings["scenario"],
        )

        if mode == "Benchmark":
            # Head-to-Head Comparative Benchmark
            self._run_benchmark_thread(settings, demand)
        else:
            # Single controller run
            self.current_runner = SimulationRunner(
                mode=mode,
                use_gui=settings["use_gui"],
                duration=settings["duration"],
                seed=42,
                demand=demand
            )
            self.current_runner.run_async(
                step_callback=self._on_step_telemetry,
                done_callback=self._on_single_done,
                status_callback=self.controls.log_message,
                error_callback=self._on_simulation_error
            )

    def _run_benchmark_thread(self, settings: Dict[str, Any], demand: DemandProfile):
        """Execute Baseline and Adaptive sequentially under identical conditions."""
        def worker():
            try:
                self.current_runner = PairedSimulationRunner(
                    use_gui=settings["use_gui"],
                    duration=settings["duration"],
                    seed=42,
                    demand=demand
                )
                self.baseline_summary, self.adaptive_summary = self.current_runner.run_sync(
                    step_callback=self._on_paired_step,
                    status_callback=self.controls.log_message
                )
                self.baseline_df = self.current_runner.fixed_runner.metrics.get_dataframe()
                self.adaptive_df = self.current_runner.adaptive_runner.metrics.get_dataframe()
                if self._stop_benchmark:
                    self.after(0, lambda: self.lbl_badge.configure(text="STOPPED", text_color=COLORS["red"]))
                    return
                self.after(0, self._on_benchmark_completed)
            except Exception as exc:
                self._on_simulation_error(exc)

        self._benchmark_thread = threading.Thread(target=worker, daemon=True)
        self._benchmark_thread.start()

    def _on_paired_step(self, fixed: StepTelemetry, adaptive: StepTelemetry):
        """Render both real controller streams at their shared simulation time."""
        def update_ui():
            self.card_time.update_value(f"{adaptive.time:.0f}")
            self.card_active.update_value(f"{adaptive.active_vehicles}")
            self.card_wait.update_value(f"{adaptive.avg_waiting_time:.1f}")
            self.card_queue.update_value(f"{adaptive.total_queue:.1f}")
            self.charts.update_pair_step(fixed, adaptive)
        self.after(0, update_ui)

    def _on_benchmark_completed(self):
        """Callback when dual benchmark completes."""
        self.lbl_badge.configure(text="BENCHMARK COMPLETED", text_color=COLORS["green"])
        self.controls.log_message("Dual comparative benchmark complete.")

        # Render comparison curves
        self.charts.render_comparison(self.baseline_df, self.adaptive_df)

        # Calculate improvement
        if self.baseline_summary and self.adaptive_summary:
            base_wait = self.baseline_summary.mean_waiting_time
            adapt_wait = self.adaptive_summary.mean_waiting_time
            if base_wait > 1e-4:
                reduction = ((base_wait - adapt_wait) / base_wait) * 100.0
                self.card_reduction.update_value(f"{reduction:.1f}%")

            # Auto export comparison benchmark
            scenario = self.current_runner.demand.scenario if self.current_runner else "balanced"
            duration = self.current_runner.duration if self.current_runner else 0
            csv_path = export_comparison_csv(
                self.baseline_summary, self.adaptive_summary,
                filename=f"comparison_{scenario}_42_{duration}.csv"
            )
            json_path = export_comparison_json(
                self.baseline_summary,
                self.adaptive_summary,
                metadata={
                    "scenario": scenario,
                    "seed": self.current_runner.seed if self.current_runner else 42,
                    "duration_sim_seconds": duration,
                },
                decisions=getattr(self.current_runner.controller, "decision_log", []) if self.current_runner else [],
                filename=f"comparison_{scenario}_42_{duration}.json",
            )
            self.controls.log_message(f"Comparative CSV exported: {csv_path.name}")
            self.controls.log_message(f"JSON run record exported: {json_path.name}")
            self.controls.log_message(
                f"Summary: Baseline Wait={base_wait:.1f}s -> Adaptive Wait={adapt_wait:.1f}s ({reduction:.1f}% reduction)"
            )

    def _on_step_telemetry(self, t: StepTelemetry):
        """Thread-safe UI update dispatched on each simulation second."""
        def update_ui():
            self.card_time.update_value(f"{t.time:.0f}")
            self.card_active.update_value(f"{t.active_vehicles}")
            self.card_wait.update_value(f"{t.avg_waiting_time:.1f}")
            self.card_queue.update_value(f"{t.total_queue:.1f}")
            self.charts.update_live_step(t.time, t.total_queue, t.accumulated_delay)

        self.after(0, update_ui)

    def _on_single_done(self, summary: SimulationSummary):
        def update_ui():
            self.lbl_badge.configure(text="COMPLETED", text_color=COLORS["green"])
            self.controls.log_message(
                f"Run finished: Completed={summary.total_completed_trips}, Mean Wait={summary.mean_waiting_time:.2f}s, Delay={summary.total_accumulated_delay:.1f} veh·s"
            )
        self.after(0, update_ui)

    def _on_simulation_error(self, error: Exception):
        """Surface SUMO startup/runtime failures as an explicit disconnected state."""
        def update_ui():
            self.lbl_badge.configure(text="DISCONNECTED", text_color=COLORS["red"])
            self.controls.log_message(f"Disconnected: {error}")
        self.after(0, update_ui)

    def handle_pause(self):
        if self.current_runner and self.current_runner.is_running:
            self.current_runner.pause()
            self.lbl_badge.configure(text="PAUSED", text_color=COLORS["amber"])
            self.controls.log_message("Simulation paused.")

    def handle_resume(self):
        if self.current_runner and self.current_runner.is_running:
            self.current_runner.resume()
            self.lbl_badge.configure(text="RUNNING", text_color=COLORS["amber"])
            self.controls.log_message("Simulation resumed.")

    def handle_stop(self):
        self._stop_benchmark = True
        if self.current_runner:
            self.current_runner.stop()
            self.lbl_badge.configure(text="STOPPED", text_color=COLORS["red"])
            self.controls.log_message("Simulation stop requested.")

    def handle_reset(self):
        """Stop an active run and clear the displayed telemetry."""
        self._stop_benchmark = True
        if self.current_runner and self.current_runner.is_running:
            self.current_runner.stop()
        self.baseline_summary = None
        self.adaptive_summary = None
        self.baseline_df = pd.DataFrame()
        self.adaptive_df = pd.DataFrame()
        self.charts.reset()
        for card in (self.card_time, self.card_active, self.card_wait, self.card_queue):
            card.update_value("0")
        self.card_reduction.update_value("--")
        self.lbl_badge.configure(text="SYSTEM READY", text_color=COLORS["green"])
        self.controls.log_message("Reset requested. Wait for the current SUMO process to stop before starting again.")

    def _toggle_pause(self, _event=None):
        if self.current_runner and self.current_runner.is_running:
            self.handle_resume() if self.current_runner.is_paused else self.handle_pause()
        return "break"

    def _reset_shortcut(self, _event=None):
        self.handle_reset()
        return "break"

    def handle_export(self):
        """Export latest metrics to CSV."""
        if self.baseline_summary and self.adaptive_summary:
            scenario = self.current_runner.demand.scenario if self.current_runner else "balanced"
            duration = self.current_runner.duration if self.current_runner else 0
            out_file = export_comparison_csv(
                self.baseline_summary, self.adaptive_summary,
                filename=f"comparison_{scenario}_42_{duration}.csv"
            )
            self.controls.log_message(f"Exported comparative benchmark: {out_file.name}")
            json_file = export_comparison_json(
                self.baseline_summary,
                self.adaptive_summary,
                metadata={
                    "scenario": scenario,
                    "seed": self.current_runner.seed if self.current_runner else 42,
                    "duration_sim_seconds": duration,
                },
                decisions=getattr(self.current_runner.controller, "decision_log", []) if self.current_runner else [],
                filename=f"comparison_{scenario}_42_{duration}.json",
            )
            self.controls.log_message(f"Exported JSON run record: {json_file.name}")
        elif self.current_runner:
            runner = self.current_runner
            scenario = runner.demand.scenario.replace(" ", "_")
            filename = f"telemetry_{runner.mode.lower()}_{scenario}_{runner.seed}_{runner.duration}.csv"
            out_file = runner.metrics.export_csv(filename)
            self.controls.log_message(f"Exported telemetry CSV: {out_file.name}")
        else:
            self.controls.log_message("No completed simulation data available to export.")


def launch_app():
    """Application entrypoint."""
    app = TrafficOptimizerApp()
    app.mainloop()


if __name__ == "__main__":
    launch_app()
