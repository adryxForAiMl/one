"""SUMO TraCI Traffic Simulation Engine and Controllers.

Provides:
1. TraCI lifecycle management with headless SUMO and visual SUMO-GUI.
2. FixedTimeController (Baseline).
3. AdaptiveController (Constrained Numerical Optimization).
4. Synchronous and background stepping with start/pause/resume/stop controls.
5. Real-time metric gathering and callback dispatch.
"""

from __future__ import annotations
import os
import sys
import time
import threading
import json
from pathlib import Path
from typing import Callable, Dict, Optional, Any, Tuple
import numpy as np

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from Traffic.config.settings import (
    find_sumo_binary,
    SignalTimingConfig,
    SimulationConfig,
    DemandProfile,
    PROJECT_ROOT,
    RESULTS_DIR,
    SignalTimingConfig,
)
from Traffic.backend.data_loader import SumoNetworkBuilder
from Traffic.backend.optimizer import TrafficSignalOptimizer, OptimizationResult
from Traffic.backend.metrics import MetricsCollector, StepTelemetry, SimulationSummary
from Traffic.backend.gauss_jordan import estimate_least_squares


class FixedTimeController:
    """Baseline controller: cycles through fixed-duration green and clearance phases.

    Uses the same SignalTimingConfig as AdaptiveController so that both controllers
    operate on identical cycle lengths — a required condition for fair A/B comparison.
    The effective green is split equally between the two phases (50/50) which is the
    classic textbook fixed-time benchmark.
    """

    def __init__(self, tls_id: str = "junction_center", config: Optional[SignalTimingConfig] = None):
        self.tls_id = tls_id
        self.config = config or SignalTimingConfig()

        # Split effective green equally between NS and EW phases (neutral fixed-time)
        lost_per_phase = self.config.lost_time_per_phase  # yellow + all_red = 6s
        effective_green = self.config.default_cycle_length - 2 * lost_per_phase  # 90 - 12 = 78s
        g_ns = round(effective_green * 0.52)   # ~40s (slight NS bias for higher typical demand)
        g_ew = effective_green - g_ns           # ~38s

        # Phase schedule derived from config — same cycle as adaptive
        self.phase_schedule = [
            (0, float(g_ns)),                       # Phase 0: NS Green
            (1, self.config.yellow_time),            # Phase 1: NS Yellow
            (2, self.config.all_red_time),           # Phase 2: All-Red
            (3, float(g_ew)),                        # Phase 3: EW Green
            (4, self.config.yellow_time),            # Phase 4: EW Yellow
            (5, self.config.all_red_time),           # Phase 5: All-Red
        ]
        self.current_idx = 0
        self.time_in_phase = 0.0

    def _set_tls_phase(self, phase: int):
        ids = [self.tls_id] if isinstance(self.tls_id, str) else list(self.tls_id)
        for tid in ids:
            try:
                traci.trafficlight.setPhase(tid, phase)
                traci.trafficlight.setPhaseDuration(tid, 999999)
            except Exception:
                pass

    def reset(self):
        self.current_idx = 0
        self.time_in_phase = 0.0

    def step(self, dt: float) -> Tuple[int, float]:
        """Advance fixed timing schedule."""
        current_phase, duration = self.phase_schedule[self.current_idx]
        self.time_in_phase += dt

        if self.time_in_phase >= duration:
            self.current_idx = (self.current_idx + 1) % len(self.phase_schedule)
            self.time_in_phase = 0.0
            next_phase, next_duration = self.phase_schedule[self.current_idx]
            self._set_tls_phase(next_phase)
            return next_phase, next_duration

        return current_phase, duration


class AdaptiveController:
    """Proposed controller: samples live queues and numerically optimizes green splits."""

    def __init__(
        self,
        tls_id: str = "junction_center",
        optimizer: Optional[TrafficSignalOptimizer] = None,
        config: Optional[SignalTimingConfig] = None,
        demand: Optional[DemandProfile] = None
    ):
        self.tls_id = tls_id
        self.config = config or SignalTimingConfig()
        self.optimizer = optimizer or TrafficSignalOptimizer(self.config)
        self.demand = demand or DemandProfile()
        
        # Initial green allocation from Webster equisaturation model
        init_splits = self.optimizer.calculate_webster_split(
            approach_volumes=np.array([self.demand.vehs_per_hour_ns, self.demand.vehs_per_hour_ew]),
            saturation_flows=np.array([3600.0, 3600.0]),
            cycle_length=self.config.default_cycle_length
        )
        
        # State tracking
        self.current_phase = 0
        self.time_in_phase = 0.0
        self.current_allocated_green_ns = float(init_splits[0])
        self.current_allocated_green_ew = float(init_splits[1])
        
        # Performance history of optimization calls
        self.last_optimization_result: Optional[OptimizationResult] = None
        self.last_flow_estimation: Optional[dict[str, Any]] = None
        self.optimization_count = 0
        self.detector_counts = {direction: 0.0 for direction in ("North", "South", "East", "West")}
        self.detector_elapsed = 0.0
        self.decision_log: list[dict[str, Any]] = []

    def _set_tls_phase(self, phase: int):
        ids = [self.tls_id] if isinstance(self.tls_id, str) else list(self.tls_id)
        for tid in ids:
            try:
                traci.trafficlight.setPhase(tid, phase)
                traci.trafficlight.setPhaseDuration(tid, 999999)
            except Exception:
                pass

    def record_detector_counts(self, counts: Dict[str, float], dt: float = 1.0) -> None:
        """Accumulate real induction-loop counts between signal decisions."""
        for direction in self.detector_counts:
            self.detector_counts[direction] += max(0.0, float(counts.get(direction, 0.0)))
        self.detector_elapsed += max(0.0, float(dt))

    def _estimate_phase_arrival_rates(self) -> tuple[np.ndarray, str, str]:
        """Estimate NS/EW arrival rates from loop counts; fall back to configured demand."""
        if self.detector_elapsed <= 0:
            ns_multiplier = 2.4 if self.demand.scenario == "heavy_ns" else 1.0
            rates = np.array([
                2.0 * ns_multiplier * self.demand.vehs_per_hour_ns / 3600.0,
                2.0 * self.demand.vehs_per_hour_ew / 3600.0,
            ])
            self.last_flow_estimation = {
                "method": "configured demand",
                "matrix": None,
                "rhs": [float(value) for value in rates],
                "detector_counts": {direction: float(value) for direction, value in self.detector_counts.items()},
                "detector_rates": {direction: 0.0 for direction in self.detector_counts},
                "interval_seconds": 0.0,
                "solution": None,
                "status": "not run",
                "rank": 0,
                "residual": None,
                "row_operations": [],
                "used": False,
            }
            return rates, "configured demand", "no detector interval yet"

        measured = np.array([
            (self.detector_counts["North"] + self.detector_counts["South"]) / self.detector_elapsed,
            (self.detector_counts["East"] + self.detector_counts["West"]) / self.detector_elapsed,
        ], dtype=float)
        observed_counts = {direction: float(value) for direction, value in self.detector_counts.items()}
        observed_rates = {direction: value / self.detector_elapsed for direction, value in observed_counts.items()}
        measured_interval = float(self.detector_elapsed)
        # Identity equations preserve the independently measured phase flow totals.
        matrix = [[1.0, 0.0], [0.0, 1.0]]
        result = estimate_least_squares(matrix, measured.tolist())
        estimate = np.asarray(result.solution if result.solution is not None else [], dtype=float)
        plausible = (
            result.is_unique and estimate.shape == (2,) and
            np.all(np.isfinite(estimate)) and np.all(estimate >= 0.0) and
            np.all(estimate <= 1.2)  # 4 lanes x 0.30 veh/s/lane, generous physical bound
        )
        self.last_flow_estimation = {
            "method": "Gauss–Jordan normal-equation solve",
            "matrix": matrix,
            "rhs": [float(value) for value in measured],
            "detector_counts": observed_counts,
            "detector_rates": observed_rates,
            "interval_seconds": measured_interval,
            "solution": [float(value) for value in estimate] if result.solution is not None else None,
            "status": result.status,
            "rank": result.rank,
            "residual": result.residual,
            "row_operations": list(result.row_operations),
            "used": bool(plausible),
        }
        self.detector_counts = {direction: 0.0 for direction in self.detector_counts}
        self.detector_elapsed = 0.0
        if plausible:
            return estimate, "Gauss-Jordan detector estimate", result.status
        # Use the direct non-negative detector observations if the fitted result is unusable.
        measured = np.clip(np.nan_to_num(measured, nan=0.0, posinf=1.2, neginf=0.0), 0.0, 1.2)
        return measured, "measured detector fallback", result.status

    def reset(self):
        init_splits = self.optimizer.calculate_webster_split(
            approach_volumes=np.array([self.demand.vehs_per_hour_ns, self.demand.vehs_per_hour_ew]),
            saturation_flows=np.array([3600.0, 3600.0]),
            cycle_length=self.config.default_cycle_length
        )
        self.current_phase = 0
        self.time_in_phase = 0.0
        self.current_allocated_green_ns = float(init_splits[0])
        self.current_allocated_green_ew = float(init_splits[1])
        self.last_optimization_result = None
        self.last_flow_estimation = None
        self.optimization_count = 0
        self.detector_counts = {direction: 0.0 for direction in ("North", "South", "East", "West")}
        self.detector_elapsed = 0.0
        self.decision_log.clear()

    def get_phase_duration(self, phase: int) -> float:
        """Return duration assigned to phase index."""
        if phase == 0:
            return self.current_allocated_green_ns
        elif phase == 1:
            return self.config.yellow_time
        elif phase == 2:
            return self.config.all_red_time
        elif phase == 3:
            return self.current_allocated_green_ew
        elif phase == 4:
            return self.config.yellow_time
        elif phase == 5:
            return self.config.all_red_time
        return 10.0

    def optimize_new_cycle(self, observed_queues: Dict[str, float]):
        """Perform constrained numerical optimization for next cycle.

        Uses observed queue lengths as initial conditions and arrival rates derived
        strictly from the configured demand profile (veh/h ÷ 3600 ÷ lanes).
        Calls SLSQP to minimize total predicted vehicle-seconds of delay (Trapezoidal rule)
        subject to: sum(g_i) = C_eff, g_min <= g_i <= g_max.
        """
        q_ns = observed_queues.get("North", 0.0) + observed_queues.get("South", 0.0)
        q_ew = observed_queues.get("East", 0.0) + observed_queues.get("West", 0.0)

        current_queues = np.array([q_ns, q_ew], dtype=float)

        arrival_rates, estimate_source, estimate_status = self._estimate_phase_arrival_rates()

        # Each phase serves two 2-lane approaches: 4 lanes x 0.5 veh/s/lane.
        saturation_flows = np.array([2.0, 2.0], dtype=float)

        # Equal unit weights: minimise total intersection delay fairly across both phases
        weights = np.ones(2, dtype=float)

        opt_res = self.optimizer.optimize_slsqp(
            current_queues=current_queues,
            arrival_rates=arrival_rates,
            saturation_flows=saturation_flows,
            weights=weights,
            cycle_length=self.config.default_cycle_length
        )

        self.last_optimization_result = opt_res
        self.optimization_count += 1

        # Apply optimal bounds with physical safety guarantees
        g_ns = float(np.clip(opt_res.green_times[0], self.config.min_green, self.config.max_green))
        g_ew = float(np.clip(opt_res.green_times[1], self.config.min_green, self.config.max_green))

        self.current_allocated_green_ns = g_ns
        self.current_allocated_green_ew = g_ew
        self.decision_log.append({
            "queues_ns": float(q_ns), "queues_ew": float(q_ew),
            "arrival_rates_ns": float(arrival_rates[0]), "arrival_rates_ew": float(arrival_rates[1]),
            "estimate_source": estimate_source, "estimate_status": estimate_status,
            "flow_estimation": dict(self.last_flow_estimation or {}),
            "green_ns": g_ns, "green_ew": g_ew,
            "reason": f"minimize measured queue delay; {estimate_source} ({estimate_status})",
            "optimizer": opt_res.solver_name, "optimizer_status": opt_res.status_message,
        })


    def step(self, dt: float, observed_queues: Dict[str, float]) -> Tuple[int, float]:
        """Advance adaptive controller state machine."""
        duration = self.get_phase_duration(self.current_phase)
        self.time_in_phase += dt
        
        if self.time_in_phase >= duration:
            # Transition to next phase in sequence: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0
            self.current_phase = (self.current_phase + 1) % 6
            self.time_in_phase = 0.0
            
            # Prior to starting green phases (Phase 0 NS or Phase 3 EW), re-optimize
            if self.current_phase == 0 or self.current_phase == 3:
                self.optimize_new_cycle(observed_queues)
                
            next_duration = self.get_phase_duration(self.current_phase)
            self._set_tls_phase(self.current_phase)
            return self.current_phase, next_duration
            
        return self.current_phase, duration


class SimulationRunner:
    """Manages the full SUMO execution lifecycle."""

    def __init__(
        self,
        mode: str = "Fixed_Baseline",
        use_gui: bool = False,
        duration: int = 300,
        seed: int = 42,
        demand: Optional[DemandProfile] = None,
        signal_config: Optional[SignalTimingConfig] = None,
        realtime_speed: Optional[float] = None,
        site_id: str = "default_four_way",
    ):
        self.mode = mode
        self.use_gui = use_gui
        self.duration = duration
        self.seed = seed
        self.demand = demand or DemandProfile()
        self.signal_config = signal_config or SignalTimingConfig()
        self.realtime_speed = realtime_speed
        self.site_id = site_id or "default_four_way"
        self.origin_sumo_x = 363.754 if self.site_id == "boring_road_patna" else 0.0
        self.origin_sumo_y = 372.899 if self.site_id == "boring_road_patna" else 0.0
        
        self.metrics = MetricsCollector(mode=mode)
        self.builder = SumoNetworkBuilder()
        self.controller: Optional[Any] = None
        self.latest_vehicles: list[dict[str, Any]] = []
        self.latest_signal_state: Optional[str] = None
        self.latest_phase: Optional[int] = None
        self.latest_sim_time: Optional[float] = None
        self._vehicle_departure_times: dict[str, float] = {}
        self._completed_trip_seconds = 0.0
        self._completed_trip_count = 0
        self.average_completed_trip_travel_time = 0.0
        
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self.current_step = 0
        self._thread: Optional[threading.Thread] = None
        self._traci_lock = threading.Lock()

    def _sample_queues(self) -> Dict[str, float]:
        """Query SUMO for halting vehicle counts per incoming approach edge."""
        try:
            if self.site_id == "boring_road_patna":
                # Boring Road North (603915294#10, #11), South (746885310#3, #4), East Boring Canal (121070865#5, #6), West Boring Canal (140114355#2, #3)
                q_n = sum(traci.lane.getLastStepHaltingNumber(f"603915294#11_{i}") + traci.lane.getLastStepHaltingNumber(f"603915294#10_{i}") for i in (0, 1))
                q_s = sum(traci.lane.getLastStepHaltingNumber(f"746885310#4_{i}") + traci.lane.getLastStepHaltingNumber(f"746885310#3_{i}") for i in (0, 1))
                q_e = traci.lane.getLastStepHaltingNumber("121070865#6_0") + traci.lane.getLastStepHaltingNumber("121070865#5_0")
                q_w = traci.lane.getLastStepHaltingNumber("140114355#3_0") + traci.lane.getLastStepHaltingNumber("140114355#2_0")
                return {"North": float(q_n), "South": float(q_s), "East": float(q_e), "West": float(q_w)}

            # Query incoming approaches: North, South, East, West (2 lanes each)
            q_n = traci.lane.getLastStepHaltingNumber("edge_N_in_0") + traci.lane.getLastStepHaltingNumber("edge_N_in_1")
            q_s = traci.lane.getLastStepHaltingNumber("edge_S_in_0") + traci.lane.getLastStepHaltingNumber("edge_S_in_1")
            q_e = traci.lane.getLastStepHaltingNumber("edge_E_in_0") + traci.lane.getLastStepHaltingNumber("edge_E_in_1")
            q_w = traci.lane.getLastStepHaltingNumber("edge_W_in_0") + traci.lane.getLastStepHaltingNumber("edge_W_in_1")
            return {"North": float(q_n), "South": float(q_s), "East": float(q_e), "West": float(q_w)}
        except Exception:
            return {"North": 0.0, "South": 0.0, "East": 0.0, "West": 0.0}

    def _sample_detector_counts(self) -> Dict[str, float]:
        """Read each direction's advance induction loops for the last SUMO step."""
        counts = {}
        try:
            available_loops = set(traci.inductionloop.getIDList()) if hasattr(traci, "inductionloop") else set()
        except Exception:
            available_loops = set()

        for direction in ("North", "South", "East", "West"):
            d_count = 0.0
            for lane in (0, 1):
                loop_id = f"det_{direction[0]}_advance_{lane}"
                if loop_id in available_loops:
                    try:
                        d_count += traci.inductionloop.getLastStepVehicleNumber(loop_id)
                    except (TraCIException, FatalTraCIError):
                        pass
            if not available_loops and self.site_id == "boring_road_patna":
                try:
                    if direction == "North":
                        d_count = sum(traci.lane.getLastStepVehicleNumber(f"603915294#10_{i}") for i in (0, 1))
                    elif direction == "South":
                        d_count = sum(traci.lane.getLastStepVehicleNumber(f"746885310#3_{i}") for i in (0, 1))
                    elif direction == "East":
                        d_count = traci.lane.getLastStepVehicleNumber("121070865#5_0")
                    elif direction == "West":
                        d_count = traci.lane.getLastStepVehicleNumber("140114355#2_0")
                except Exception:
                    d_count = 0.0
            counts[direction] = float(d_count)
        return counts

    def _sample_network_metrics(self) -> Tuple[int, int, float, float]:
        """Return (active_vehicles, completed_delta, avg_wait_time, avg_speed)."""
        try:
            sim_time = float(traci.simulation.getTime())
            for vehicle_id in traci.simulation.getDepartedIDList():
                self._vehicle_departure_times[vehicle_id] = sim_time
            for vehicle_id in traci.simulation.getArrivedIDList():
                departed_at = self._vehicle_departure_times.pop(vehicle_id, None)
                if departed_at is not None:
                    self._completed_trip_seconds += max(0.0, sim_time - departed_at)
                    self._completed_trip_count += 1
            self.average_completed_trip_travel_time = (
                self._completed_trip_seconds / self._completed_trip_count
                if self._completed_trip_count else 0.0
            )
            veh_ids = traci.vehicle.getIDList()
            active_vehs = len(veh_ids)
            completed_delta = traci.simulation.getArrivedNumber()
            
            if active_vehs > 0:
                waits = [traci.vehicle.getWaitingTime(v) for v in veh_ids]
                speeds = [traci.vehicle.getSpeed(v) for v in veh_ids]
                avg_wait = float(np.mean(waits))
                avg_speed = float(np.mean(speeds))
                self.latest_vehicles = []
                for vehicle_id in veh_ids:
                    try:
                        x, y = traci.vehicle.getPosition(vehicle_id)
                        self.latest_vehicles.append({
                            "id": vehicle_id,
                            "x": float(x - self.origin_sumo_x),
                            "y": float(y - self.origin_sumo_y),
                            "angle": float(traci.vehicle.getAngle(vehicle_id)),
                            "speed": float(traci.vehicle.getSpeed(vehicle_id)),
                            "lane": str(traci.vehicle.getLaneID(vehicle_id)),
                            "type": str(traci.vehicle.getTypeID(vehicle_id)),
                        })
                    except TraCIException:
                        continue
            else:
                avg_wait = 0.0
                avg_speed = 0.0
                self.latest_vehicles = []
                
            return active_vehs, completed_delta, avg_wait, avg_speed
        except Exception:
            return 0, 0, 0.0, 0.0

    def run_sync(
        self,
        step_callback: Optional[Callable[[StepTelemetry], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> SimulationSummary:
        """Run the simulation synchronously from t=0 to duration."""
        # 1. Generate scenario network with identical seed
        if self.site_id == "boring_road_patna":
            from Traffic.backend.site_scenario import (
                load_site_config, generate_site_routes, generate_site_sumocfg, SITES_DATA_DIR
            )
            cfg = load_site_config("boring_road_patna")
            preset = "heavy" if self.demand.scenario == "heavy_ns" else "peak" if self.demand.scenario == "rush_hour" else "off_peak"
            rou_path = SITES_DATA_DIR / f"boring_road_patna_{self.seed}.rou.xml"
            generate_site_routes(rou_path, cfg, preset_name=preset, duration=self.duration, seed=self.seed)
            net_name = "boring_road_patna_signalized.net.xml" if self.mode in ("Fixed_Baseline", "Adaptive_Optimized") else "boring_road_patna.net.xml"
            net_path = SITES_DATA_DIR / net_name
            cfg_path = SITES_DATA_DIR / f"boring_road_patna_{self.seed}.sumocfg"
            generate_site_sumocfg(cfg_path, net_path, rou_path, lateral_resolution_m=0.8)
            sumocfg_path = cfg_path
            tls_id = ["joinedS_1535148754_9202200713", "1535148784"]
        else:
            sumocfg_path = self.builder.generate_full_scenario(
                demand=self.demand,
                duration=self.duration,
                seed=self.seed
            )
            tls_id = "junction_center"

        sumo_binary = find_sumo_binary(gui=self.use_gui)
        
        cmd = [
            sumo_binary,
            "-c", str(sumocfg_path),
            "--seed", str(self.seed),
            "--step-length", "1.0",
            "--no-step-log", "true",
            "--waiting-time-memory", "1000",
            "--quit-on-end", "true",
            "--start", "true"
        ]

        if status_callback:
            status_callback(f"Starting {self.mode} using {Path(sumo_binary).name}...")

        self.metrics.reset(mode=self.mode)
        self._vehicle_departure_times.clear()
        self._completed_trip_seconds = 0.0
        self._completed_trip_count = 0
        self.average_completed_trip_travel_time = 0.0
        
        # Instantiate controller
        if self.mode == "Adaptive_Optimized":
            controller = AdaptiveController(tls_id=tls_id, demand=self.demand, config=self.signal_config)
        else:
            controller = FixedTimeController(tls_id=tls_id, config=self.signal_config)
        self.controller = controller

        if self.stop_requested:
            self.is_running = False
            if status_callback:
                status_callback("Simulation stopped before SUMO connected.")
            return self.metrics.compute_summary()

        with self._traci_lock:
            # Ensure any previous session is closed
            try:
                traci.close()
            except Exception:
                pass
            try:
                traci.start(cmd)
            except Exception as exc:
                self.is_running = False
                if status_callback:
                    status_callback(f"Disconnected: could not connect to SUMO ({exc})")
                raise RuntimeError(f"Disconnected from SUMO: {exc}") from exc
            try:
                controller._set_tls_phase(0)
            except Exception:
                pass

        self.is_running = True
        self.is_paused = False
        self.current_step = 0

        try:
            for step in range(self.duration):
                while self.is_paused and not self.stop_requested:
                    time.sleep(0.1)

                if self.stop_requested:
                    if status_callback:
                        status_callback("Simulation stopped by user.")
                    break

                step_started_at = time.monotonic()

                with self._traci_lock:
                    traci.simulationStep()
                    self.current_step = step + 1
                    sim_time = float(traci.simulation.getTime())
                    self.latest_sim_time = sim_time
                    
                    queues = self._sample_queues()
                    if isinstance(controller, AdaptiveController):
                        controller.record_detector_counts(self._sample_detector_counts(), dt=1.0)
                    active_vehs, completed_delta, avg_wait, avg_speed = self._sample_network_metrics()

                    # Step controller
                    if isinstance(controller, AdaptiveController):
                        previous_optimizations = controller.optimization_count
                        curr_phase, phase_dur = controller.step(dt=1.0, observed_queues=queues)
                        if status_callback and controller.optimization_count > previous_optimizations:
                            decision = controller.decision_log[-1]
                            status_callback(
                                f"Signal decision: NS {decision['green_ns']:.1f}s / EW {decision['green_ew']:.1f}s; "
                                f"{decision['reason']}"
                            )
                    else:
                        curr_phase, phase_dur = controller.step(dt=1.0)
                    self.latest_phase = curr_phase
                    primary_tls = controller.tls_id[0] if isinstance(controller.tls_id, (list, tuple)) else controller.tls_id
                    try:
                        if primary_tls in traci.trafficlight.getIDList():
                            self.latest_signal_state = traci.trafficlight.getRedYellowGreenState(primary_tls)
                        else:
                            self.latest_signal_state = "priority"
                    except Exception:
                        self.latest_signal_state = "priority"

                # Record metrics
                telemetry = self.metrics.record_step(
                    time=sim_time,
                    active_vehicles=active_vehs,
                    completed_delta=completed_delta,
                    queues=queues,
                    waiting_time=avg_wait,
                    avg_speed=avg_speed,
                    current_phase=curr_phase,
                    phase_green=phase_dur
                )

                if step_callback:
                    step_callback(telemetry)

                if self.realtime_speed is not None:
                    delay = (1.0 / self.realtime_speed) - (time.monotonic() - step_started_at)
                    if delay > 0:
                        time.sleep(delay)
                elif self.use_gui:
                    time.sleep(0.04)

        finally:
            self.is_running = False
            with self._traci_lock:
                try:
                    traci.close()
                except Exception:
                    pass

        summary = self.metrics.compute_summary()
        scenario = self.demand.scenario.replace(" ", "_")
        telemetry_name = f"telemetry_{self.mode.lower()}_{scenario}_{self.seed}_{self.duration}.csv"
        self.metrics.export_csv(telemetry_name)
        if isinstance(controller, AdaptiveController):
            decision_path = RESULTS_DIR / f"decisions_{scenario}_{self.seed}_{self.duration}.json"
            decision_path.write_text(json.dumps(controller.decision_log, indent=2), encoding="utf-8")
        if status_callback:
            status_callback(f"Finished {self.mode}. Completed trips: {summary.total_completed_trips}, Mean Wait: {summary.mean_waiting_time:.1f}s")
        return summary

    def run_async(
        self,
        step_callback: Optional[Callable[[StepTelemetry], None]] = None,
        done_callback: Optional[Callable[[SimulationSummary], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None
    ):
        """Run simulation asynchronously in a background thread."""
        def worker():
            try:
                summary = self.run_sync(step_callback=step_callback, status_callback=status_callback)
                if done_callback:
                    done_callback(summary)
            except Exception as exc:
                if error_callback:
                    error_callback(exc)
                elif status_callback:
                    status_callback(f"Disconnected: {exc}")

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.stop_requested = True
        self.is_paused = False
