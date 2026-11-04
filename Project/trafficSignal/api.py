"""Typed local API and live WebSocket for the SUMO traffic simulator."""

from __future__ import annotations

import argparse
import asyncio
import sys
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

# Support importing this module directly when the project directory is the deployment root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from Traffic.backend.paired_simulation import PairedSimulationRunner
from Traffic.backend.simulation import SimulationRunner
from Traffic.config.settings import DemandProfile, SignalTimingConfig


class RunMode(str, Enum):
    fixed = "fixed"
    adaptive = "adaptive"
    compare = "compare"


class ScenarioName(str, Enum):
    balanced = "balanced"
    heavy_ns = "heavy_ns"
    sudden_surge = "sudden_surge"
    rush_hour = "rush_hour"


class VehicleState(BaseModel):
    vehicle_id: str
    x_m: float
    y_m: float
    angle_degrees: float
    speed_mps: float
    lane_id: str
    type_id: str


class SignalState(BaseModel):
    phase: int
    phase_state: str
    green_seconds_remaining: Optional[float] = None


class ControllerConfig(BaseModel):
    min_green_seconds: float = Field(default=10.0, gt=0, le=60)
    max_green_seconds: float = Field(default=60.0, gt=0, le=90)
    yellow_seconds: float = Field(default=4.0, ge=0.5, le=10)
    all_red_seconds: float = Field(default=2.0, ge=0.5, le=10)
    cycle_seconds: float = Field(default=90.0, ge=45, le=150)

    @model_validator(mode="after")
    def validate_cycle(self):
        if self.max_green_seconds < self.min_green_seconds:
            raise ValueError("max_green_seconds must be >= min_green_seconds")
        min_cycle = 2 * self.min_green_seconds + 2 * (self.yellow_seconds + self.all_red_seconds)
        if self.cycle_seconds < min_cycle:
            raise ValueError("cycle_seconds cannot fit two minimum greens and clearance intervals")
        return self

    def to_settings(self) -> SignalTimingConfig:
        return SignalTimingConfig(
            min_green=self.min_green_seconds,
            max_green=self.max_green_seconds,
            yellow_time=self.yellow_seconds,
            all_red_time=self.all_red_seconds,
            lost_time_per_phase=self.yellow_seconds + self.all_red_seconds,
            default_cycle_length=self.cycle_seconds,
        )


class SimulationStartRequest(BaseModel):
    mode: RunMode = RunMode.compare
    scenario: ScenarioName = ScenarioName.balanced
    seed: int = Field(default=42, ge=0, le=2_147_483_647)
    duration_seconds: int = Field(default=120, ge=1, le=3600)
    north_south_veh_per_hour: int = Field(default=600, ge=0, le=7200)
    east_west_veh_per_hour: int = Field(default=450, ge=0, le=7200)
    use_gui: bool = False
    speed_multiplier: float = Field(default=8.0, ge=0.5, le=8.0)
    controller: ControllerConfig = Field(default_factory=ControllerConfig)
    site_id: str = "default_four_way"


class MetricsState(BaseModel):
    active_vehicles: int
    completed_vehicles: int
    total_queue_vehicles: float
    queues_by_approach: dict[str, float]
    average_wait_seconds: float
    accumulated_delay_vehicle_seconds: float
    average_speed_mps: float
    phase_green_seconds: float
    average_completed_trip_travel_time_seconds: float = 0.0


class RunSummaryState(BaseModel):
    total_completed_trips: int
    mean_queue_length: float
    peak_95th_queue_length: float
    mean_waiting_time: float
    total_accumulated_delay: float
    mean_speed_kmh: float
    average_completed_trip_travel_time_seconds: float


class SolverResultState(BaseModel):
    solver: str
    status: str
    converged: bool
    green_seconds: list[float]
    objective_value: float
    reason: str


class FlowEstimationState(BaseModel):
    method: str
    matrix: Optional[list[list[float]]] = None
    rhs: list[float] = Field(default_factory=list)
    detector_counts: dict[str, float] = Field(default_factory=dict)
    detector_rates: dict[str, float] = Field(default_factory=dict)
    interval_seconds: float = 0.0
    solution: Optional[list[float]] = None
    status: str
    rank: int
    residual: Optional[float] = None
    row_operations: list[str] = Field(default_factory=list)
    used: bool


class ControllerLiveState(BaseModel):
    mode: str
    metrics: MetricsState
    signal: Optional[SignalState] = None
    vehicles: list[VehicleState] = Field(default_factory=list)
    solver: Optional[SolverResultState] = None
    flow_estimation: Optional[FlowEstimationState] = None
    decision_reason: Optional[str] = None


class LiveState(BaseModel):
    status: str
    scenario: Optional[str] = None
    site_id: str = "default_four_way"
    disclaimer: str = "Synthetic four-way baseline"
    attribution: str = "© OpenStreetMap contributors"
    seed: Optional[int] = None
    speed_multiplier: float = 1.0
    simulation_time_seconds: Optional[float] = None
    wall_elapsed_seconds: Optional[float] = None
    controllers: dict[str, ControllerLiveState] = Field(default_factory=dict)
    results_summary: dict[str, RunSummaryState] = Field(default_factory=dict)
    error: Optional[str] = None


def _controller_snapshot(mode: str, telemetry, runner) -> ControllerLiveState:
    queues = {
        "North": float(telemetry.queue_north),
        "South": float(telemetry.queue_south),
        "East": float(telemetry.queue_east),
        "West": float(telemetry.queue_west),
    }
    vehicles = [
        VehicleState(
            vehicle_id=item["id"], x_m=item["x"], y_m=item["y"],
            angle_degrees=item["angle"], speed_mps=item["speed"],
            lane_id=item["lane"], type_id=item["type"],
        )
        for item in runner.latest_vehicles
    ]
    phase_state = runner.latest_signal_state
    controller = getattr(runner, "controller", None)
    green_remaining = None
    if telemetry.current_phase in {0, 3} and controller is not None:
        phase_elapsed = getattr(controller, "time_in_phase", None)
        if phase_elapsed is not None:
            green_remaining = max(0.0, float(telemetry.phase_green_time) - float(phase_elapsed))
    signal = SignalState(phase=telemetry.current_phase, phase_state=phase_state,
                         green_seconds_remaining=green_remaining) if phase_state is not None else None
    metrics = MetricsState(
        active_vehicles=telemetry.active_vehicles,
        completed_vehicles=telemetry.completed_vehicles,
        total_queue_vehicles=telemetry.total_queue,
        queues_by_approach=queues,
        average_wait_seconds=telemetry.avg_waiting_time,
        accumulated_delay_vehicle_seconds=telemetry.accumulated_delay,
        average_speed_mps=telemetry.avg_speed,
        phase_green_seconds=telemetry.phase_green_time,
        average_completed_trip_travel_time_seconds=float(getattr(runner, "average_completed_trip_travel_time", 0.0)),
    )
    optimization = getattr(controller, "last_optimization_result", None)
    solver = None
    flow_estimation = None
    decision_reason = None
    if optimization is not None:
        solver = SolverResultState(
            solver=optimization.solver_name,
            status=optimization.status_message,
            converged=optimization.converged,
            green_seconds=[float(value) for value in optimization.green_times],
            objective_value=float(optimization.objective_value),
            reason=optimization.status_message,
        )
    decisions = getattr(controller, "decision_log", [])
    if decisions:
        decision = decisions[-1]
        if decision.get("flow_estimation"):
            flow_estimation = FlowEstimationState(**decision["flow_estimation"])
        decision_reason = (
            f"NS {decision['green_ns']:.1f}s / EW {decision['green_ew']:.1f}s; "
            f"queues NS {decision['queues_ns']:.0f}, EW {decision['queues_ew']:.0f}; "
            f"flow {decision['estimate_source']} ({decision['estimate_status']}); "
            f"{decision['reason']}"
        )
    return ControllerLiveState(mode=mode, metrics=metrics, signal=signal, vehicles=vehicles,
                               solver=solver, flow_estimation=flow_estimation,
                               decision_reason=decision_reason)


class SimulationManager:
    """Own one real simulation run and provide thread-safe snapshots to API clients."""

    def __init__(self):
        self._lock = threading.RLock()
        self._generation = 0
        self._runner = None
        self._started_at: Optional[float] = None
        self._stop_requested = False
        self._reset_pending = False
        self._state = LiveState(status="idle")

    def snapshot(self) -> LiveState:
        with self._lock:
            state = self._state.model_copy(deep=True)
            if self._started_at is not None and state.status not in {"idle", "completed", "stopped", "disconnected"}:
                state.wall_elapsed_seconds = time.monotonic() - self._started_at
            return state

    def start(self, request: SimulationStartRequest) -> LiveState:
        with self._lock:
            if self._state.status in {"connecting", "connected", "paused", "stopping"}:
                raise RuntimeError("A simulation is already running")
            self._generation += 1
            generation = self._generation
            self._stop_requested = False
            self._reset_pending = False
            self._started_at = time.monotonic()
            disclaimer = (
                "Simulation on real road geometry with assumed demand"
                if request.site_id == "boring_road_patna"
                else "Synthetic four-way baseline"
            )
            self._state = LiveState(
                status="connecting", scenario=request.scenario.value,
                site_id=request.site_id,
                disclaimer=disclaimer,
                attribution="© OpenStreetMap contributors",
                seed=request.seed,
                speed_multiplier=request.speed_multiplier,
                simulation_time_seconds=None, wall_elapsed_seconds=0.0, controllers={}, error=None,
            )

            demand = DemandProfile(
                name=request.scenario.value,
                scenario=request.scenario.value,
                vehs_per_hour_ns=request.north_south_veh_per_hour,
                vehs_per_hour_ew=request.east_west_veh_per_hour,
            )
            signal_config = request.controller.to_settings()
            if request.mode == RunMode.compare:
                runner = PairedSimulationRunner(
                    use_gui=request.use_gui, duration=request.duration_seconds, seed=request.seed,
                    demand=demand, signal_config=signal_config, realtime_speed=request.speed_multiplier,
                    site_id=request.site_id,
                )
                runner.run_async(
                    step_callback=lambda fixed, adaptive: self._on_pair(generation, runner, fixed, adaptive),
                    done_callback=lambda fixed, adaptive: self._on_done(generation, {
                        "fixed": (fixed, runner.fixed_runner), "adaptive": (adaptive, runner.adaptive_runner),
                    }),
                    status_callback=lambda message: self._on_status(generation, message),
                    error_callback=lambda exc: self._on_error(generation, exc),
                )
            else:
                mode = "Fixed_Baseline" if request.mode == RunMode.fixed else "Adaptive_Optimized"
                runner = SimulationRunner(
                    mode=mode, use_gui=request.use_gui, duration=request.duration_seconds,
                    seed=request.seed, demand=demand, signal_config=signal_config,
                    realtime_speed=request.speed_multiplier,
                    site_id=request.site_id,
                )
                runner.run_async(
                    step_callback=lambda telemetry: self._on_single(generation, runner, telemetry),
                    done_callback=lambda summary: self._on_done(generation, {
                        "fixed" if runner.mode == "Fixed_Baseline" else "adaptive": (summary, runner),
                    }),
                    status_callback=lambda message: self._on_status(generation, message),
                    error_callback=lambda exc: self._on_error(generation, exc),
                )
            self._runner = runner
            return self.snapshot()

    def _update_time(self, telemetry):
        self._state.simulation_time_seconds = float(telemetry.time)
        if self._started_at is not None:
            self._state.wall_elapsed_seconds = time.monotonic() - self._started_at

    def _on_single(self, generation: int, runner: SimulationRunner, telemetry):
        with self._lock:
            if generation != self._generation:
                return
            key = "fixed" if runner.mode == "Fixed_Baseline" else "adaptive"
            self._state.controllers = {key: _controller_snapshot(key, telemetry, runner)}
            self._update_time(telemetry)
            if self._state.status == "connecting":
                self._state.status = "connected"

    def _on_pair(self, generation: int, runner: PairedSimulationRunner, fixed, adaptive):
        with self._lock:
            if generation != self._generation:
                return
            self._state.controllers = {
                "fixed": _controller_snapshot("fixed", fixed, runner.fixed_runner),
                "adaptive": _controller_snapshot("adaptive", adaptive, runner.adaptive_runner),
            }
            self._update_time(adaptive)
            if self._state.status == "connecting":
                self._state.status = "connected"

    def _on_status(self, generation: int, message: str):
        with self._lock:
            if generation != self._generation:
                return
            if message.startswith("Disconnected:"):
                self._state.status = "disconnected"
                self._state.error = message
            elif message.startswith("Connected:") or message.startswith("Starting"):
                self._state.status = "connected" if message.startswith("Connected:") else "connecting"
            elif message.startswith("Finished"):
                self._state.status = "stopped" if self._stop_requested else "completed"

    def _on_done(self, generation: int, summaries=None):
        with self._lock:
            if generation != self._generation:
                return
            if self._reset_pending:
                self._runner = None
                self._reset_pending = False
                self._started_at = None
                self._state = LiveState(status="idle")
                return
            if summaries:
                self._state.results_summary = {
                    key: RunSummaryState(
                        total_completed_trips=int(summary.total_completed_trips),
                        mean_queue_length=float(summary.mean_queue_length),
                        peak_95th_queue_length=float(summary.peak_95th_queue_length),
                        mean_waiting_time=float(summary.mean_waiting_time),
                        total_accumulated_delay=float(summary.total_accumulated_delay),
                        mean_speed_kmh=float(summary.mean_speed_kmh),
                        average_completed_trip_travel_time_seconds=float(getattr(runner, "average_completed_trip_travel_time", 0.0)),
                    ) for key, (summary, runner) in summaries.items()
                }
            self._state.status = "stopped" if self._stop_requested else "completed"

    def _on_error(self, generation: int, error: Exception):
        with self._lock:
            if generation != self._generation:
                return
            if self._reset_pending:
                self._runner = None
                self._reset_pending = False
                self._started_at = None
                self._state = LiveState(status="idle")
                return
            self._state.status = "disconnected"
            self._state.error = str(error)

    def pause(self):
        with self._lock:
            if self._runner is None or not getattr(self._runner, "is_running", False):
                raise RuntimeError("No active simulation to pause")
            self._runner.pause()
            self._state.status = "paused"

    def resume(self):
        with self._lock:
            if self._runner is None or not getattr(self._runner, "is_running", False):
                raise RuntimeError("No active simulation to resume")
            self._runner.resume()
            self._state.status = "connected"

    def stop(self):
        with self._lock:
            if self._runner is None or self._state.status not in {"connecting", "connected", "paused"}:
                raise RuntimeError("No active simulation to stop")
            self._stop_requested = True
            self._runner.stop()
            self._state.status = "stopping"

    def reset(self):
        with self._lock:
            if self._runner is not None and self._state.status in {"connecting", "connected", "paused", "stopping"}:
                self._reset_pending = True
                self._runner.stop()
                self._state.status = "stopping"
                return
            self._generation += 1
            self._runner = None
            self._started_at = None
            self._stop_requested = False
            self._reset_pending = False
            self._state = LiveState(status="idle")


manager = SimulationManager()
app = FastAPI(title="Adaptive Traffic Signal Simulator API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173", "http://localhost:5173",
        "http://127.0.0.1:5174", "http://localhost:5174",
    ],
    allow_origin_regex=r"^https?://(?:localhost|127\.0\.0\.1):51[7-9][0-9]$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def disable_api_caching(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/state", response_model=LiveState)
def get_state():
    return manager.snapshot()


@app.post("/api/simulation/start", response_model=LiveState)
def start_simulation(request: SimulationStartRequest):
    try:
        return manager.start(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/simulation/pause", response_model=LiveState)
def pause_simulation():
    try:
        manager.pause()
        return manager.snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/simulation/resume", response_model=LiveState)
def resume_simulation():
    try:
        manager.resume()
        return manager.snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/simulation/stop", response_model=LiveState)
def stop_simulation():
    try:
        manager.stop()
        return manager.snapshot()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/simulation/reset", response_model=LiveState)
def reset_simulation():
    manager.reset()
    return manager.snapshot()


@app.get("/api/sites")
def list_sites():
    return [
        {
            "id": "default_four_way",
            "name": "Default 4-Way Intersection",
            "type": "procedural",
            "description": "Synthetic balanced 4-way intersection benchmark",
            "attribution": None,
        },
        {
            "id": "boring_road_patna",
            "name": "Boring Road Chauraha, Patna",
            "type": "real_world_osm",
            "description": "Simulation on real road geometry with assumed demand",
            "attribution": "© OpenStreetMap contributors",
        },
    ]


@app.get("/api/site/{site_id}/geometry")
def get_site_geometry(site_id: str):
    from Traffic.backend.site_scenario import extract_site_geometry
    try:
        return extract_site_geometry(site_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/site/{site_id}/provenance")
def get_site_provenance(site_id: str):
    from Traffic.backend.site_scenario import load_site_config
    try:
        cfg = load_site_config(site_id)
        return {
            "site_id": site_id,
            "display_name": cfg["site"]["display_name"]["value"],
            "attribution": cfg["map"]["attribution"]["value"],
            "disclaimer": cfg["model"]["demand"]["disclaimer"]["value"],
            "provenance": {
                k: {"value": str(v.get("value", "")), "source": v.get("source", "assumed")}
                for section in ("site", "map", "observed_osm", "model", "vtypes")
                for k, v in cfg.get(section, {}).items()
                if isinstance(v, dict)
            }
        }
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/site/{site_id}/conflicts")
def get_site_conflicts(site_id: str):
    from Traffic.backend.site_scenario import parse_net_conflicts, SITES_DATA_DIR
    net_path = SITES_DATA_DIR / f"{site_id}.net.xml"
    if not net_path.is_file():
        raise HTTPException(status_code=404, detail=f"Network for {site_id} not found")
    return parse_net_conflicts(net_path)


@app.websocket("/ws/live")
async def live_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(manager.snapshot().model_dump(mode="json"))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        return


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the traffic simulator HTTP and WebSocket API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
