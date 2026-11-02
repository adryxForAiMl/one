"""Synchronized fixed/adaptive SUMO benchmark using two labeled TraCI sessions."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable, Optional

import traci

from Traffic.backend.metrics import SimulationSummary, StepTelemetry
from Traffic.backend.simulation import AdaptiveController, FixedTimeController, SimulationRunner
from Traffic.config.settings import DemandProfile, SignalTimingConfig


class PairedSimulationRunner:
    """Advance fixed and adaptive simulations in lockstep on identical arrivals."""

    def __init__(
        self,
        *,
        use_gui: bool = False,
        duration: int = 120,
        seed: int = 42,
        demand: Optional[DemandProfile] = None,
        signal_config: Optional[SignalTimingConfig] = None,
        realtime_speed: Optional[float] = None,
        site_id: str = "default_four_way",
    ):
        self.use_gui = use_gui
        self.duration = duration
        self.seed = seed
        self.demand = demand or DemandProfile()
        self.signal_config = signal_config or SignalTimingConfig()
        self.realtime_speed = realtime_speed
        self.site_id = site_id or "default_four_way"
        self.fixed_runner = SimulationRunner("Fixed_Baseline", use_gui, duration, seed, self.demand, self.signal_config, realtime_speed, site_id=self.site_id)
        self.adaptive_runner = SimulationRunner("Adaptive_Optimized", use_gui, duration, seed, self.demand, self.signal_config, realtime_speed, site_id=self.site_id)
        self.fixed_runner.metrics.reset("Fixed_Baseline")
        self.adaptive_runner.metrics.reset("Adaptive_Optimized")
        self.fixed_controller = FixedTimeController(config=self.signal_config)
        self.adaptive_controller = AdaptiveController(demand=self.demand, config=self.signal_config)
        if self.site_id == "boring_road_patna":
            self.fixed_controller.tls_id = ["joinedS_1535148754_9202200713", "1535148784"]
            self.adaptive_controller.tls_id = ["joinedS_1535148754_9202200713", "1535148784"]
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self._lock = threading.RLock()
        self._labels = (f"traffic_fixed_{id(self)}", f"traffic_adaptive_{id(self)}")

    @property
    def controller(self):
        return self.adaptive_controller

    @property
    def metrics(self):
        return self.adaptive_runner.metrics

    def _command(self, runner: SimulationRunner) -> list[str]:
        from Traffic.config.settings import find_sumo_binary

        if self.site_id == "boring_road_patna":
            from Traffic.backend.site_scenario import (
                load_site_config, generate_site_routes, generate_site_sumocfg, SITES_DATA_DIR
            )
            cfg = load_site_config("boring_road_patna")
            preset = "heavy" if self.demand.scenario == "heavy_ns" else "peak" if self.demand.scenario == "rush_hour" else "off_peak"
            rou_path = SITES_DATA_DIR / f"boring_road_patna_{self.seed}.rou.xml"
            generate_site_routes(rou_path, cfg, preset_name=preset, duration=self.duration, seed=self.seed)
            net_name = "boring_road_patna_signalized.net.xml" if runner.mode in ("Fixed_Baseline", "Adaptive_Optimized") else "boring_road_patna.net.xml"
            net_path = SITES_DATA_DIR / net_name
            cfg_path = SITES_DATA_DIR / f"boring_road_patna_{self.seed}.sumocfg"
            generate_site_sumocfg(cfg_path, net_path, rou_path, lateral_resolution_m=0.8)
            sumocfg_path = cfg_path
        else:
            sumocfg_path = runner.builder.generate_full_scenario(
                demand=self.demand, duration=self.duration, seed=self.seed
            )

        return [
            find_sumo_binary(gui=self.use_gui), "-c", str(sumocfg_path), "--seed", str(self.seed), "--step-length", "1.0", "--no-step-log", "true",
            "--waiting-time-memory", "1000", "--quit-on-end", "true", "--start", "true",
        ]

    def _step_one(self, label: str, runner: SimulationRunner, controller, adaptive: bool):
        traci.switch(label)
        traci.simulationStep()
        sim_time = float(traci.simulation.getTime())
        runner.latest_sim_time = sim_time
        queues = runner._sample_queues()
        if adaptive:
            controller.record_detector_counts(runner._sample_detector_counts(), 1.0)
        active, completed, avg_wait, avg_speed = runner._sample_network_metrics()
        if adaptive:
            old_count = controller.optimization_count
            phase, phase_duration = controller.step(1.0, queues)
            decision = controller.decision_log[-1] if controller.optimization_count > old_count else None
        else:
            phase, phase_duration = controller.step(1.0)
            decision = None
        telemetry = runner.metrics.record_step(
            time=sim_time, active_vehicles=active, completed_delta=completed, queues=queues,
            waiting_time=avg_wait, avg_speed=avg_speed, current_phase=phase, phase_green=phase_duration,
        )
        runner.latest_phase = phase
        primary_tls = controller.tls_id[0] if isinstance(controller.tls_id, (list, tuple)) else controller.tls_id
        try:
            if primary_tls in traci.trafficlight.getIDList():
                runner.latest_signal_state = traci.trafficlight.getRedYellowGreenState(primary_tls)
            else:
                runner.latest_signal_state = "priority"
        except Exception:
            runner.latest_signal_state = "priority"
        return telemetry, decision

    def run_sync(
        self,
        step_callback: Optional[Callable[[StepTelemetry, StepTelemetry], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> tuple[SimulationSummary, SimulationSummary]:
        fixed_label, adaptive_label = self._labels
        started = []
        try:
            fixed_command = self._command(self.fixed_runner)
            adaptive_command = self._command(self.adaptive_runner)
            self.fixed_runner.metrics.reset("Fixed_Baseline")
            self.adaptive_runner.metrics.reset("Adaptive_Optimized")
            for runner in (self.fixed_runner, self.adaptive_runner):
                runner._vehicle_departure_times.clear()
                runner._completed_trip_seconds = 0.0
                runner._completed_trip_count = 0
                runner.average_completed_trip_travel_time = 0.0
            self.fixed_runner.controller = self.fixed_controller
            self.adaptive_runner.controller = self.adaptive_controller
            self.adaptive_controller.reset()
            if self.stop_requested:
                return (self.fixed_runner.metrics.compute_summary(),
                        self.adaptive_runner.metrics.compute_summary())
            with self._lock:
                traci.start(fixed_command, label=fixed_label)
                started.append(fixed_label)
                traci.switch(fixed_label)
                try:
                    self.fixed_controller._set_tls_phase(0)
                except Exception:
                    pass
                if self.stop_requested:
                    return (self.fixed_runner.metrics.compute_summary(),
                            self.adaptive_runner.metrics.compute_summary())
                traci.start(adaptive_command, label=adaptive_label)
                started.append(adaptive_label)
                traci.switch(adaptive_label)
                try:
                    self.adaptive_controller._set_tls_phase(0)
                except Exception:
                    pass

            self.is_running = True
            if status_callback:
                status_callback("Connected: fixed and adaptive SUMO runs are stepping together.")
            for _ in range(self.duration):
                while self.is_paused and not self.stop_requested:
                    time.sleep(0.05)
                if self.stop_requested:
                    break
                step_started_at = time.monotonic()
                with self._lock:
                    fixed_telemetry, _ = self._step_one(fixed_label, self.fixed_runner, self.fixed_controller, False)
                    adaptive_telemetry, decision = self._step_one(adaptive_label, self.adaptive_runner, self.adaptive_controller, True)
                if decision and status_callback:
                    status_callback(
                        f"Adaptive decision: NS {decision['green_ns']:.1f}s / EW {decision['green_ew']:.1f}s; "
                        f"{decision['reason']}"
                    )
                if step_callback:
                    step_callback(fixed_telemetry, adaptive_telemetry)
                if self.realtime_speed is not None:
                    delay = (1.0 / self.realtime_speed) - (time.monotonic() - step_started_at)
                    if delay > 0:
                        time.sleep(delay)
                elif self.use_gui:
                    time.sleep(0.04)
        except Exception as exc:
            self.is_running = False
            if status_callback:
                status_callback(f"Disconnected: paired SUMO run failed ({exc})")
            raise RuntimeError(f"Disconnected from paired SUMO sessions: {exc}") from exc
        finally:
            self.is_running = False
            for label in reversed(started):
                try:
                    traci.switch(label)
                    traci.close()
                except Exception:
                    pass

        fixed_summary = self.fixed_runner.metrics.compute_summary()
        adaptive_summary = self.adaptive_runner.metrics.compute_summary()
        scenario = self.demand.scenario.replace(" ", "_")
        self.fixed_runner.metrics.export_csv(f"telemetry_fixed_baseline_{scenario}_{self.seed}_{self.duration}.csv")
        self.adaptive_runner.metrics.export_csv(f"telemetry_adaptive_optimized_{scenario}_{self.seed}_{self.duration}.csv")
        return fixed_summary, adaptive_summary

    def run_async(
        self,
        *,
        step_callback: Optional[Callable[[StepTelemetry, StepTelemetry], None]] = None,
        done_callback: Optional[Callable[[SimulationSummary, SimulationSummary], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
    ):
        def worker():
            try:
                summaries = self.run_sync(step_callback, status_callback)
                if done_callback:
                    done_callback(*summaries)
            except Exception as exc:
                if error_callback:
                    error_callback(exc)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.stop_requested = True
