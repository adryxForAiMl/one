import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Activity, AlertTriangle, Check, CircleHelp, Download, Gauge, Pause, Play, RotateCcw, Sparkles, Square, WifiOff, Trash2, History, TrendingDown, Info } from "lucide-react";
import type { ControllerLiveState, LiveState, Sample, SiteGeometry, SiteOption } from "./types";
import type { CameraPreset, RenderQuality } from "./trafficScene";
import { VectorMiniMap } from "./VectorMiniMap";
import { RealVsAssumedPanel } from "./RealVsAssumedPanel";

const TrafficScene = lazy(() => import("./TrafficSceneView").then((module) => ({ default: module.TrafficScene })));
const SharedTrafficSceneGrid = lazy(() => import("./TrafficSceneView").then((module) => ({ default: module.SharedTrafficSceneGrid })));

const API_ROOT = import.meta.env.VITE_TRAFFIC_API ?? "";
const WS_ROOT = API_ROOT
  ? API_ROOT.replace(/^http/, "ws")
  : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;

type Mode = "compare" | "adaptive" | "fixed";
type Quality = RenderQuality;
type RunSummary = LiveState["results_summary"];
type RunRecord = { id: string; saved_at: string; scenario: string | null; seed: number | null; duration: number | null; summary: RunSummary };

function format(value: number | null | undefined, digits = 1) {
  return value == null || !Number.isFinite(value) ? "—" : value.toFixed(digits);
}

function Metric({ label, fixed, adaptive, unit, digits = 1 }: { label: string; fixed?: number; adaptive?: number; unit: string; digits?: number }) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-values">
        <div><span className="metric-value">{format(fixed, digits)}</span><span className="metric-unit">{unit}</span></div>
        <div><span className="metric-value adaptive-value">{format(adaptive, digits)}</span><span className="metric-unit">{unit}</span></div>
      </div>
      <div className="metric-legend"><span>Fixed</span><span>Adaptive</span></div>
    </div>
  );
}

function Trend({ title, samples, fixedKey, adaptiveKey, unit }: { title: string; samples: Sample[]; fixedKey: keyof Sample; adaptiveKey: keyof Sample; unit: string }) {
  const width = 540;
  const height = 150;
  const values = samples.flatMap((sample) => [sample[fixedKey], sample[adaptiveKey]]).filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const max = Math.max(1, ...values);
  const pointString = (key: keyof Sample) => samples.map((sample, index) => {
    const value = sample[key];
    if (typeof value !== "number") return null;
    const x = samples.length < 2 ? width : (index / (samples.length - 1)) * width;
    const y = height - (value / max) * (height - 12) - 6;
    return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
  }).filter(Boolean).join(" ");

  return (
    <section className="trend-card">
      <div className="trend-title-row"><div><span className="section-kicker">SIMULATION TIME · {unit}</span><h3>{title}</h3></div><div className="trend-legend"><span><i className="legend-fixed" />Fixed</span><span><i className="legend-adaptive" />Adaptive</span></div></div>
      {samples.length ? (
        <svg className="trend-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title} from live simulation telemetry`}>
          {[0.25, 0.5, 0.75, 1].map((fraction) => <line key={fraction} x1="0" x2={width} y1={height * fraction} y2={height * fraction} className="grid-line" />)}
          <path d={pointString(fixedKey)} className="trend-line fixed-line" />
          <path d={pointString(adaptiveKey)} className="trend-line adaptive-line" />
        </svg>
      ) : <div className="chart-empty">Charts populate when SUMO reports its first sample.</div>}
    </section>
  );
}

function download(name: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const signalPhases = ["N–S green", "N–S yellow", "All red", "E–W green", "E–W yellow", "All red"];

function SignalPlan({ controller }: { controller: ControllerLiveState | null }) {
  const phase = controller?.signal?.phase ?? -1;
  const greenRemaining = controller?.signal?.green_seconds_remaining;
  return (
    <section className="signal-plan-card" aria-label="Live signal phase sequence">
      <div className="signal-plan-heading"><span className="section-kicker">SIGNAL SEQUENCE</span><b>{phase >= 0 ? `P${phase} · ${signalPhases[phase] ?? "Unknown phase"}` : "Waiting for signal"}</b></div>
      <div className="phase-track">{signalPhases.map((name, index) => <div key={`${name}-${index}`} className={`phase-step phase-step-${index} ${phase === index ? "is-current" : ""}`} title={`Phase ${index}: ${name}`}><i /> <span>{index}</span></div>)}</div>
      <div className="signal-plan-foot"><span>Next: {phase >= 0 ? signalPhases[(phase + 1) % signalPhases.length] : "—"}</span><b>{phase < 0 ? "Waiting for timing" : greenRemaining == null ? "Clearance phase" : `${greenRemaining.toFixed(0)}s green remaining`}</b></div>
    </section>
  );
}

function DetectorNetwork({ controller }: { controller: ControllerLiveState | null }) {
  const flow = controller?.flow_estimation;
  const queues = controller?.metrics.queues_by_approach ?? {};
  const hasMetrics = Boolean(controller?.metrics);
  return (
    <section className="reference-card detector-card">
      <div className="reference-card-heading"><div><span className="section-kicker">LIVE DETECTOR NETWORK</span><h3>Approach activity</h3></div><span className="live-tag"><i />SUMO</span></div>
      <div className="detector-map" role="group" aria-label="Live induction loop measurements by approach">
        <div className="detector-node detector-north"><b>North</b><span>{hasMetrics ? `${Math.round(queues.North ?? 0)} queued` : "— queued"}</span><small>{format(flow?.detector_rates?.North, 2)} veh/s · {format(flow?.detector_counts?.North, 0)} loops</small></div>
        <div className="detector-node detector-west"><b>West</b><span>{hasMetrics ? `${Math.round(queues.West ?? 0)} queued` : "— queued"}</span><small>{format(flow?.detector_rates?.West, 2)} veh/s · {format(flow?.detector_counts?.West, 0)} loops</small></div>
        <div className="detector-junction"><Activity size={17} /><span>SUMO<br />junction</span></div>
        <div className="detector-node detector-east"><b>East</b><span>{hasMetrics ? `${Math.round(queues.East ?? 0)} queued` : "— queued"}</span><small>{format(flow?.detector_rates?.East, 2)} veh/s · {format(flow?.detector_counts?.East, 0)} loops</small></div>
        <div className="detector-node detector-south"><b>South</b><span>{hasMetrics ? `${Math.round(queues.South ?? 0)} queued` : "— queued"}</span><small>{format(flow?.detector_rates?.South, 2)} veh/s · {format(flow?.detector_counts?.South, 0)} loops</small></div>
      </div>
      <p className="reference-card-note">{flow?.interval_seconds ? `Loop measurements use the latest ${format(flow.interval_seconds, 0)}s adaptive window.` : "Waiting for the first detector measurement window."}</p>
    </section>
  );
}

function FleetMix({ controller }: { controller: ControllerLiveState | null }) {
  const counts = new Map<string, number>();
  controller?.vehicles.forEach((vehicle) => counts.set(vehicle.type_id, (counts.get(vehicle.type_id) ?? 0) + 1));
  const total = controller?.vehicles.length ?? 0;
  const order = ["hatchback", "sedan", "suv", "van", "bus", "truck"];
  return (
    <section className="reference-card fleet-card">
      <div className="reference-card-heading"><div><span className="section-kicker">LIVE VEHICLE COUNTS</span><h3>Fleet mix</h3></div><b className="fleet-total">{total} active</b></div>
      {total ? <div className="fleet-list">{order.map((type) => {
        const count = counts.get(type) ?? 0;
        return <div className="fleet-row" key={type}><span>{type}</span><div className="fleet-bar"><i style={{ width: `${(count / total) * 100}%` }} /></div><b>{count}</b></div>;
      })}</div> : <div className="reference-empty">Fleet counts appear when SUMO reports active vehicles.</div>}
      <p className="reference-card-note">Grouped from active SUMO vehicle IDs and type IDs.</p>
    </section>
  );
}

function TrafficAlerts({ controller }: { controller: ControllerLiveState | null }) {
  const metrics = controller?.metrics;
  const alerts = Object.entries(metrics?.queues_by_approach ?? {}).filter(([, queue]) => queue >= 10).map(([direction, queue]) => ({
    label: `${direction} approach queue is ${Math.round(queue)} vehicles`, severity: queue >= 20 ? "critical" : "watch",
  }));
  if (metrics && metrics.average_wait_seconds >= 30) alerts.push({ label: `Mean waiting time is ${metrics.average_wait_seconds.toFixed(1)} seconds`, severity: "watch" });
  return (
    <section className="reference-card alerts-card">
      <div className="reference-card-heading"><div><span className="section-kicker">RULE-BASED MONITORING</span><h3>Traffic alerts</h3></div><span className={`alert-count ${alerts.length ? "has-alerts" : ""}`}>{alerts.length} active</span></div>
      <p className="reference-card-note">Watch rules: queue ≥10 vehicles per approach or mean wait ≥30s.</p>
      {alerts.length ? <ul className="traffic-alert-list">{alerts.map((alert, index) => <li className={`alert-${alert.severity}`} key={`${alert.label}-${index}`}><i />{alert.label}</li>)}</ul> : metrics ? <div className="no-alerts"><Check size={15} />No queue or wait threshold alerts.</div> : <div className="reference-empty">Alerts appear when live SUMO metrics arrive.</div>}
    </section>
  );
}

function RunHistory({ runs, onClear }: { runs: RunRecord[]; onClear: () => void }) {
  const [selected, setSelected] = useState<RunRecord | null>(null);
  const [expanded, setExpanded] = useState(false);
  return (
    <section className="reference-card history-card">
      <div className="reference-card-heading"><div><span className="section-kicker">LOCAL RUN ARCHIVE</span><h3>Run history</h3></div><button className="history-toggle" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}><History size={13} />{runs.length} saved</button></div>
      {expanded && <>
        {runs.length ? <>
          <div className="history-list">{runs.map((run) => {
            const adaptiveWait = run.summary.adaptive?.mean_waiting_time;
            return <button className={`history-item ${selected?.id === run.id ? "selected" : ""}`} key={run.id} onClick={() => setSelected(run)}>
              <span><b>{run.scenario ?? "Scenario"}</b><small>{new Date(run.saved_at).toLocaleString()} · seed {run.seed ?? "—"}</small></span>
              <strong>{adaptiveWait == null ? "—" : `${adaptiveWait.toFixed(1)}s`}<small>adaptive wait</small></strong>
            </button>;
          })}</div>
          {selected && <div className="history-detail"><b>{selected.scenario} · seed {selected.seed}</b><span>Fixed wait {format(selected.summary.fixed?.mean_waiting_time)}s → Adaptive {format(selected.summary.adaptive?.mean_waiting_time)}s</span><button onClick={() => download(`traffic-run-${selected.seed ?? "result"}.json`, JSON.stringify(selected, null, 2), "application/json")}><Download size={12} /> Export selected run</button></div>}
          <button className="history-clear" onClick={() => { setSelected(null); onClear(); }}><Trash2 size={12} />Clear saved history</button>
        </> : <div className="reference-empty">Completed runs will be saved on this device.</div>}
      </>}
      {!expanded && <p className="reference-card-note">Completed run summaries are saved on this device for quick review.</p>}
    </section>
  );
}

function PerformanceInsights({ summary }: { summary: RunSummary }) {
  const fixed = summary.fixed;
  const adaptive = summary.adaptive;
  if (!fixed || !adaptive) return null;
  const waitDelta = fixed.mean_waiting_time - adaptive.mean_waiting_time;
  const delayDelta = fixed.total_accumulated_delay - adaptive.total_accumulated_delay;
  const tripsDelta = adaptive.total_completed_trips - fixed.total_completed_trips;
  const reduction = (before: number, after: number) => before > 0 ? ((before - after) / before) * 100 : null;
  const waitReduction = reduction(fixed.mean_waiting_time, adaptive.mean_waiting_time);
  const delayReduction = reduction(fixed.total_accumulated_delay, adaptive.total_accumulated_delay);
  return <section className="insights-card panel">
    <div className="trend-title-row"><div><span className="section-kicker">MEASURED RUN COMPARISON</span><h3>What changed with adaptive control?</h3></div><TrendingDown size={17} /></div>
    <div className="insight-grid">
      <div><span>Mean wait</span><b className={waitDelta >= 0 ? "insight-positive" : "insight-negative"}>{waitDelta >= 0 ? "−" : "+"}{Math.abs(waitDelta).toFixed(1)}s</b><small>{waitReduction === null ? "Baseline wait was zero" : `${Math.abs(waitReduction).toFixed(1)}% ${waitDelta >= 0 ? "lower" : "higher"} than fixed`}</small></div>
      <div><span>Total delay</span><b className={delayDelta >= 0 ? "insight-positive" : "insight-negative"}>{delayDelta >= 0 ? "−" : "+"}{Math.abs(delayDelta).toFixed(0)} veh·s</b><small>{delayReduction === null ? "Baseline delay was zero" : `${Math.abs(delayReduction).toFixed(1)}% ${delayDelta >= 0 ? "lower" : "higher"} than fixed`}</small></div>
      <div><span>Completed trips</span><b className={tripsDelta >= 0 ? "insight-positive" : "insight-negative"}>{tripsDelta >= 0 ? "+" : "−"}{Math.abs(tripsDelta)}</b><small>{tripsDelta >= 0 ? "more" : "fewer"} trips than fixed</small></div>
    </div>
  </section>;
}

export default function App() {
  const [live, setLive] = useState<LiveState | null>(null);
  const [socketConnected, setSocketConnected] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [scenario, setScenario] = useState("balanced");
  const [mode, setMode] = useState<Mode>("compare");
  const [durationText, setDurationText] = useState("120");
  const [seedText, setSeedText] = useState("42");
  const [speed, setSpeed] = useState(8);
  const [northSouthDemand, setNorthSouthDemand] = useState("600");
  const [eastWestDemand, setEastWestDemand] = useState("450");
  const [quality, setQuality] = useState<Quality>("medium");
  const [cameraPreset, setCameraPreset] = useState<CameraPreset>("overview");
  const [adaptiveResolution, setAdaptiveResolution] = useState(true);
  const [samples, setSamples] = useState<Sample[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const lastSimTime = useRef<number | null>(null);
  const lastReason = useRef<string | null>(null);
  const runStartedAt = useRef<string | null>(null);
  const lastSavedRun = useRef<string | null>(null);
  const [runHistory, setRunHistory] = useState<RunRecord[]>(() => {
    try { const saved = localStorage.getItem("trafficSignal.runHistory.v1"); const parsed: unknown = saved ? JSON.parse(saved) : []; return Array.isArray(parsed) ? parsed as RunRecord[] : []; } catch { return []; }
  });

  const [siteId, setSiteId] = useState("default_four_way");
  const [sites, setSites] = useState<SiteOption[]>([
    { id: "default_four_way", name: "Default 4-Way Intersection", type: "procedural", description: "Synthetic balanced 4-way intersection benchmark", attribution: null },
    { id: "boring_road_patna", name: "Boring Road Chauraha, Patna", type: "real_world_osm", description: "Simulation on real road geometry with assumed demand", attribution: "© OpenStreetMap contributors" },
  ]);
  const [siteGeometry, setSiteGeometry] = useState<SiteGeometry | null>(null);
  const [provenanceOpen, setProvenanceOpen] = useState(false);

  useEffect(() => {
    fetch(`${API_ROOT}/api/sites`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) setSites(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (siteId === "default_four_way") {
      setSiteGeometry(null);
      return;
    }
    fetch(`${API_ROOT}/api/site/${siteId}/geometry`)
      .then((res) => {
        if (!res.ok) throw new Error("Site geometry not available");
        return res.json();
      })
      .then((data: SiteGeometry) => setSiteGeometry(data))
      .catch((err) => {
        console.warn("Failed to load site geometry:", err);
        setSiteGeometry(null);
      });
  }, [siteId]);

  useEffect(() => {
    try { localStorage.setItem("trafficSignal.runHistory.v1", JSON.stringify(runHistory)); } catch { /* Browser storage can be disabled or full. */ }
  }, [runHistory]);

  useEffect(() => {
    const handleCameraPreset = (event: Event) => {
      const preset = (event as CustomEvent<CameraPreset>).detail;
      if (preset === "overview" || preset === "analytic" || preset === "street") setCameraPreset(preset);
    };
    window.addEventListener("traffic-camera-preset", handleCameraPreset);
    return () => window.removeEventListener("traffic-camera-preset", handleCameraPreset);
  }, []);

  useEffect(() => {
    const summary = live?.results_summary;
    if (live?.status !== "completed" || !summary || !Object.keys(summary).length || !runStartedAt.current) return;
    if (lastSavedRun.current === runStartedAt.current) return;
    const record: RunRecord = { id: runStartedAt.current, saved_at: new Date().toISOString(), scenario: live.scenario, seed: live.seed, duration: live.simulation_time_seconds, summary };
    lastSavedRun.current = record.id;
    setRunHistory((old) => [record, ...old.filter((item) => item.id !== record.id)].slice(0, 8));
  }, [live]);

  useEffect(() => {
    let stopped = false;
    let retry: number | undefined;
    let socket: WebSocket | undefined;
    const connect = () => {
      if (stopped) return;
      socket = new WebSocket(`${WS_ROOT}/ws/live`);
      socket.onopen = () => { setSocketConnected(true); setApiError(null); };
      socket.onmessage = (event) => {
        try {
          const state = JSON.parse(event.data) as LiveState;
          setLive(state);
          if (state.simulation_time_seconds !== null && state.simulation_time_seconds !== lastSimTime.current) {
            lastSimTime.current = state.simulation_time_seconds;
            const fixed = state.controllers.fixed?.metrics;
            const adaptive = state.controllers.adaptive?.metrics;
            setSamples((old) => [...old, {
              sim_time: state.simulation_time_seconds!,
              fixed_queue: fixed?.total_queue_vehicles,
              adaptive_queue: adaptive?.total_queue_vehicles,
              fixed_delay: fixed?.accumulated_delay_vehicle_seconds,
              adaptive_delay: adaptive?.accumulated_delay_vehicle_seconds,
              fixed_wait: fixed?.average_wait_seconds,
              adaptive_wait: adaptive?.average_wait_seconds,
            }].slice(-600));
          }
          const reason = state.controllers.adaptive?.decision_reason;
          if (reason && reason !== lastReason.current) {
            lastReason.current = reason;
            setEvents((old) => [`t=${format(state.simulation_time_seconds ?? undefined, 0)}s · ${reason}`, ...old].slice(0, 30));
          }
          if (state.status === "disconnected" && state.error) setApiError(state.error);
        } catch {
          setApiError("Received an unreadable state message from the API.");
        }
      };
      socket.onerror = () => setSocketConnected(false);
      socket.onclose = () => {
        setSocketConnected(false);
        if (!stopped) retry = window.setTimeout(connect, 1500);
      };
    };
    connect();
    return () => {
      stopped = true;
      if (retry) window.clearTimeout(retry);
      socket?.close();
    };
  }, []);

  const controllers = live?.controllers ?? {};
  const fixed = controllers.fixed ?? null;
  const adaptive = controllers.adaptive ?? null;
  const single = controllers.fixed ?? controllers.adaptive ?? null;
  const connected = socketConnected;
  const running = live?.status === "connected" || live?.status === "connecting" || live?.status === "paused" || live?.status === "stopping";
  const duration = Number(durationText);
  const seed = Number(seedText);
  const nsDemand = Number(northSouthDemand);
  const ewDemand = Number(eastWestDemand);
  const demandValid = northSouthDemand.trim() !== "" && eastWestDemand.trim() !== "" && Number.isInteger(nsDemand) && nsDemand >= 0 && nsDemand <= 7200 && Number.isInteger(ewDemand) && ewDemand >= 0 && ewDemand <= 7200;
  const durationValid = Number.isInteger(duration) && duration >= 15 && duration <= 3600;
  const seedValid = seedText.trim() !== "" && Number.isInteger(seed) && seed >= 0 && seed <= 2_147_483_647;
  const hasSamples = samples.length > 0;
  const progress = Math.min(100, Math.max(0, ((live?.simulation_time_seconds ?? 0) / (durationValid ? duration : 120)) * 100));
  const progressLabel = live?.status === "completed" ? "Run complete" : live?.status === "stopped" ? "Run stopped" : live?.status === "stopping" ? "Stopping…" : live?.status === "paused" ? "Paused" : live?.status === "connecting" ? "Starting SUMO…" : running ? "Simulation running" : connected ? "Ready to run" : "Connecting to simulator…";

  const request = useCallback(async (path: string, body?: unknown) => {
    setApiError(null);
    try {
      const response = await fetch(`${API_ROOT}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? `API error ${response.status}`);
      setLive(result as LiveState);
      return true;
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "The traffic API is unavailable.");
      return false;
    }
  }, []);

  const start = async () => {
    if (!durationValid || !seedValid || !demandValid) {
      setApiError("Check duration, seed, and directional demand values before starting.");
      return;
    }
    runStartedAt.current = new Date().toISOString();
    setSamples([]);
    setEvents([]);
    lastSimTime.current = null;
    lastReason.current = null;
    await request("/api/simulation/start", {
      mode, scenario, site_id: siteId, seed, duration_seconds: duration,
      speed_multiplier: speed,
      north_south_veh_per_hour: nsDemand,
      east_west_veh_per_hour: ewDemand,
    });
  };

  const startQuickDemo = async () => {
    setScenario("balanced");
    setMode("compare");
    setDurationText("60");
    setSeedText("42");
    setNorthSouthDemand("600");
    setEastWestDemand("450");
    runStartedAt.current = new Date().toISOString();
    setSamples([]);
    setEvents([]);
    lastSimTime.current = null;
    lastReason.current = null;
    await request("/api/simulation/start", {
      mode: "compare", scenario: "balanced", site_id: siteId, seed: 42, duration_seconds: 60,
      speed_multiplier: speed, north_south_veh_per_hour: 600, east_west_veh_per_hour: 450,
    });
  };

  const exportJson = () => download(`traffic_${scenario}_${seed}.json`, JSON.stringify({ latest_state: live, sampled_history: samples }, null, 2), "application/json");
  const exportPerformanceReport = () => {
    const sceneEntries = Object.entries(window.__trafficSceneDiagnostics ?? {})
      .map(([label, read]) => [label, read()] as const);
    const scenes = Object.fromEntries(sceneEntries.filter((entry) => entry[1] !== null));
    const firstScene = sceneEntries.find((entry) => entry[1] !== null)?.[1] ?? null;
    const report = {
      schema_version: 1,
      captured_at: new Date().toISOString(),
      measurement_scope: "Browser-side WebGL and Performance API readings at export time; values are not a hardware certification.",
      simulation: {
        status: live?.status ?? "disconnected",
        simulation_time_seconds: live?.simulation_time_seconds ?? null,
        scenario: live?.scenario ?? scenario,
        seed: live?.seed ?? seed,
        playback_speed_multiplier: live?.speed_multiplier ?? speed,
      },
      display: {
        viewport_width_css_px: window.innerWidth,
        viewport_height_css_px: window.innerHeight,
        device_pixel_ratio: window.devicePixelRatio,
        quality_tier: quality,
        adaptive_resolution_enabled: adaptiveResolution,
        current_resolution_scale: firstScene?.viewport.resolutionScale ?? 1,
        controller_mode: mode,
      },
      renderer: {
        architecture: mode === "compare" ? "one shared WebGLRenderer with two scissor viewports" : "single WebGLRenderer",
        counter_scope: mode === "compare" ? "renderer.info counters include both comparison scenes; the same pair total appears in each scene diagnostic" : "single scene",
        draw_calls: firstScene?.renderer.calls ?? null,
        triangles: firstScene?.renderer.triangles ?? null,
        points: firstScene?.renderer.points ?? null,
        lines: firstScene?.renderer.lines ?? null,
        geometries: firstScene?.renderer.geometries ?? null,
        textures: firstScene?.renderer.textures ?? null,
        programs: firstScene?.renderer.programs ?? null,
        gpu_vendor: firstScene?.gpu.vendor ?? null,
        gpu_renderer: firstScene?.gpu.renderer ?? null,
      },
      scenes,
      limitations: [
        "GPU memory and operating-system process memory are not exposed by this report.",
        "GPU identity can be unavailable or privacy-masked by the browser.",
        "Frame-time percentiles cover the in-memory sample window reported by each scene.",
      ],
    };
    download(`traffic_performance_${quality}_${Date.now()}.json`, JSON.stringify(report, null, 2), "application/json");
  };
  const exportCsv = () => {
    if (!hasSamples) return;
    const rows = ["simulation_time_seconds,fixed_queue,adaptive_queue,fixed_delay_vehicle_seconds,adaptive_delay_vehicle_seconds,fixed_wait_seconds,adaptive_wait_seconds"];
    samples.forEach((sample) => rows.push([
      sample.sim_time, sample.fixed_queue ?? "", sample.adaptive_queue ?? "",
      sample.fixed_delay ?? "", sample.adaptive_delay ?? "", sample.fixed_wait ?? "", sample.adaptive_wait ?? "",
    ].join(",")));
    download(`traffic_${scenario}_${seed}.csv`, rows.join("\n"), "text/csv");
  };

  const scenarioDescription: Record<string, string> = {
    balanced: "Steady traffic from every direction.",
    heavy_ns: "More traffic travels north–south.",
    sudden_surge: "Traffic increases partway through the run.",
    rush_hour: "High demand from all directions.",
  };
  const modeDescription = mode === "compare"
    ? "Same traffic for a fair side-by-side comparison."
    : mode === "adaptive" ? "Queue-responsive signal timing." : "Repeating signal timing.";
  const fixedMetrics = fixed?.metrics;
  const adaptiveMetrics = adaptive?.metrics;
  const singleMetrics = single?.metrics;

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to simulation controls and results</a>
      <header className="topbar">
        <a className="brand" href="#main-content" aria-label="Traffic control center home">
          <span className="brand-icon"><Activity size={20} strokeWidth={2.2} /></span>
          <span><strong>Traffic</strong><small>CONTROL CENTER</small></span>
        </a>
        <div className="topbar-center"><span role="status" aria-live="polite" className={`connection-pill ${connected && live?.status !== "disconnected" ? "is-connected" : "is-disconnected"}`}><i aria-hidden="true" />{live?.status === "disconnected" ? "disconnected" : connected ? live?.status ?? "connected" : "disconnected"}</span><span className="topbar-divider" /><span className="clock-label">SIM <b>{live?.simulation_time_seconds === null || live?.simulation_time_seconds === undefined ? "—" : `${live.simulation_time_seconds.toFixed(0)}s`}</b></span><span className="clock-label">WALL <b>{format(live?.wall_elapsed_seconds ?? undefined, 1)}s</b></span><span className="clock-label">SPEED <b>{(live?.speed_multiplier ?? speed)}×</b></span></div>
        <div className="topbar-actions">
          <button className="icon-button" aria-label="Download performance report as JSON" title="Download FPS, frame-time percentiles, renderer counters, and GPU information" onClick={exportPerformanceReport}><Gauge size={17} aria-hidden="true" /></button>
          <button className="icon-button" aria-label="Download current state and observed history as JSON" title="Download current state and observed history as JSON" onClick={exportJson}><Download size={17} aria-hidden="true" /></button>
          <button className="icon-button" aria-label="Download observed telemetry history as CSV" title="Download observed telemetry history as CSV" disabled={!hasSamples} onClick={exportCsv}><Activity size={17} aria-hidden="true" /></button>
          <a className="icon-button help-button" aria-label="Open API documentation in a new tab" href={`${API_ROOT}/docs`} target="_blank" rel="noreferrer" title="Open typed API documentation"><CircleHelp size={17} aria-hidden="true" /></a>
        </div>
      </header>

      <main id="main-content" className="workspace">
        <aside className="control-panel panel">
          <div className="panel-heading"><div><span className="section-kicker">EXPERIMENT</span><h1>Run setup</h1></div><span className="seed-tag">SEED {seedValid ? seed : "—"}</span></div>

          <label className="field-label" htmlFor="site-select">Intersection site</label>
          <select id="site-select" value={siteId} disabled={running} onChange={(event) => setSiteId(event.target.value)}>
            {sites.map((site) => (
              <option key={site.id} value={site.id}>{site.name}</option>
            ))}
          </select>
          {siteId !== "default_four_way" ? (
            <div className="site-disclaimer-box">
              <div className="disclaimer-title">
                <AlertTriangle size={13} className="disclaimer-icon" />
                <span>Simulation on real road geometry with assumed demand</span>
              </div>
              <p className="disclaimer-sub">
                Geometry from OpenStreetMap. Demand and signals are uncalibrated redesigns.
              </p>
              <button
                type="button"
                className="provenance-trigger-btn"
                onClick={() => setProvenanceOpen(true)}
              >
                <Info size={12} /> View real vs assumed tags
              </button>
            </div>
          ) : (
            <p className="field-help">Procedural four-way intersection benchmark.</p>
          )}

          <label className="field-label" htmlFor="scenario">Traffic scenario</label>
          <select id="scenario" value={scenario} disabled={running} onChange={(event) => setScenario(event.target.value)}>
            <option value="balanced">Balanced</option><option value="heavy_ns">Heavy north–south</option><option value="sudden_surge">Sudden surge</option><option value="rush_hour">Rush hour</option>
          </select>
          <p className="field-help">{scenarioDescription[scenario]}</p>
          <label className="field-label" htmlFor="mode">Controller view</label>
          <select id="mode" value={mode} disabled={running} onChange={(event) => setMode(event.target.value as Mode)}>
            <option value="compare">Fixed vs adaptive</option><option value="adaptive">Adaptive only</option><option value="fixed">Fixed only</option>
          </select>
          <p className="field-help">{modeDescription}</p>
          <div className="field-row">
            <div><label className="field-label" htmlFor="duration">Run length</label><div className="input-with-unit"><input id="duration" type="number" min="15" max="3600" step="15" value={durationText} aria-invalid={!durationValid} aria-describedby="duration-help" disabled={running} onChange={(event) => setDurationText(event.target.value)} onBlur={() => { if (!durationValid) setDurationText(String(Math.min(3600, Math.max(15, Number(durationText) || 120)))); }} /><span>sim s</span></div></div>
            <div><label className="field-label" htmlFor="seed">Repeatable seed</label><input id="seed" type="number" min="0" max="2147483647" value={seedText} aria-invalid={!seedValid} aria-describedby="seed-help" disabled={running} onChange={(event) => setSeedText(event.target.value)} onBlur={() => { if (!seedValid) setSeedText(String(Math.min(2_147_483_647, Math.max(0, Number(seedText) || 0)))); }} /></div>
          </div>
          <p className="field-help field-help-row"><span id="duration-help">15–3,600 simulated seconds.</span><span id="seed-help">Same seed = same traffic.</span></p>
          <span className="field-label">Directional demand</span>
          <div className="field-row demand-row">
            <div><label className="field-label" htmlFor="ns-demand">North–south</label><div className="input-with-unit"><input id="ns-demand" type="number" min="0" max="7200" step="50" value={northSouthDemand} aria-invalid={!demandValid} disabled={running} onChange={(event) => setNorthSouthDemand(event.target.value)} /><span>veh/h</span></div></div>
            <div><label className="field-label" htmlFor="ew-demand">East–west</label><div className="input-with-unit"><input id="ew-demand" type="number" min="0" max="7200" step="50" value={eastWestDemand} aria-invalid={!demandValid} disabled={running} onChange={(event) => setEastWestDemand(event.target.value)} /><span>veh/h</span></div></div>
          </div>
          <p className="field-help">Set independent arrival rates per approach (0–7,200 vehicles/hour).</p>
          <div className="quality-row"><label className="field-label" htmlFor="speed">Simulation speed</label><select id="speed" title="Simulated seconds per real second. Lower speeds are easier to watch." value={speed} disabled={running} onChange={(event) => setSpeed(Number(event.target.value))}><option value={0.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option><option value={4}>4×</option><option value={8}>8×</option></select></div>
          <details className="advanced-settings"><summary>Rendering settings</summary><div className="quality-row"><label className="field-label" htmlFor="quality">Scene quality</label><select id="quality" value={quality} onChange={(event) => setQuality(event.target.value as Quality)}><option value="ultra">Ultra</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select></div><label className="auto-resolution-toggle"><input type="checkbox" checked={adaptiveResolution} onChange={(event) => setAdaptiveResolution(event.target.checked)} />Automatic resolution</label><p className="field-help">Lowers render resolution when frame times exceed 18.2 ms; restores it gradually when performance is steady.</p></details>
          <div className="run-progress">
            <div className="run-progress-label"><span role="status" aria-live="polite">{progressLabel}</span><b>{format(live?.simulation_time_seconds, 0)}{live?.simulation_time_seconds != null ? ` / ${durationValid ? duration : 120}s` : ""}</b></div>
            <progress aria-label="Simulation progress" max="100" value={progress} />
          </div>
          <div className="action-stack">
            <button className="primary-button" disabled={!connected || running || !durationValid || !seedValid || !demandValid} onClick={start}><Play size={16} fill="currentColor" />Start simulation</button>
            <button className="demo-button" disabled={!connected || running} onClick={startQuickDemo}><Sparkles size={14} />Try a 60-second demo</button>
            <div className="action-row">
              <button className="secondary-button" disabled={!running || live?.status === "paused"} onClick={() => request("/api/simulation/pause")}><Pause size={15} />Pause</button>
              <button className="secondary-button" disabled={live?.status !== "paused"} onClick={() => request("/api/simulation/resume")}><Play size={15} />Resume</button>
            </div>
            <div className="action-row">
              <button className="danger-button" disabled={!running} onClick={() => request("/api/simulation/stop")}><Square size={14} fill="currentColor" />Stop</button>
              <button className="secondary-button" disabled={running} onClick={() => { setSamples([]); setEvents([]); request("/api/simulation/reset"); }}><RotateCcw size={15} />Reset</button>
            </div>
          </div>
          <div className="settings-note"><Check size={14} /><span>Compare mode gives both controllers identical traffic.</span></div>
          <div className="panel-bottom"><span><i className={`small-status ${socketConnected ? "online" : "offline"}`} />API {socketConnected ? "reachable" : "reconnecting"}</span><span>v1.0</span></div>
        </aside>

        <section className="main-column">
          {apiError && <div className="error-banner" role="alert"><AlertTriangle size={17} aria-hidden="true" /><span>{apiError}</span><button onClick={() => setApiError(null)} aria-label="Dismiss error">×</button></div>}
          {!socketConnected && <div className="disconnected-banner" role="status"><WifiOff size={17} aria-hidden="true" /><span>Disconnected from the simulation API. Live values are unavailable.</span><button onClick={() => { setApiError(null); window.location.reload(); }}>Reconnect</button></div>}
          {mode === "compare" ? <Suspense fallback={<div className="scene-grid"><div className="scene-loading">Preparing 3D scenes…</div></div>}>
            <SharedTrafficSceneGrid quality={quality} adaptiveResolution={adaptiveResolution}>
              <TrafficScene label="Fixed-time" snapshot={fixed} quality={quality} adaptiveResolution={adaptiveResolution} simulationTime={live?.simulation_time_seconds ?? null} speed={live?.speed_multiplier ?? speed} status={live?.status ?? "idle"} cameraPreset={cameraPreset} siteGeometry={siteGeometry} />
              <TrafficScene label="Adaptive" snapshot={adaptive} quality={quality} adaptiveResolution={adaptiveResolution} simulationTime={live?.simulation_time_seconds ?? null} speed={live?.speed_multiplier ?? speed} status={live?.status ?? "idle"} cameraPreset={cameraPreset} siteGeometry={siteGeometry} />
            </SharedTrafficSceneGrid>
          </Suspense> : <div className="scene-grid single-scene"><Suspense fallback={<div className="scene-loading">Preparing 3D scene…</div>}><TrafficScene label={mode === "fixed" ? "Fixed-time" : "Adaptive"} snapshot={single} quality={quality} adaptiveResolution={adaptiveResolution} simulationTime={live?.simulation_time_seconds ?? null} speed={live?.speed_multiplier ?? speed} status={live?.status ?? "idle"} cameraPreset={cameraPreset} siteGeometry={siteGeometry} /></Suspense></div>}
          {Object.keys(live?.results_summary ?? {}).length > 0 && <section className="result-summary panel">
            <div className="trend-title-row"><div><span className="section-kicker">COMPLETED RUN · {live?.scenario} · SEED {live?.seed}</span><h3>Performance summary</h3></div><span className="summary-duration">{format(live?.simulation_time_seconds, 0)} sim seconds</span></div>
            <div className="summary-table"><div className="summary-header"><span>Measure</span><span>Fixed</span><span>Adaptive</span></div>
              {([
                ["Mean wait", "mean_waiting_time", "s"],
                ["Mean queue", "mean_queue_length", "veh"],
                ["Accumulated delay", "total_accumulated_delay", "veh·s"],
                ["Mean trip travel", "average_completed_trip_travel_time_seconds", "s"],
                ["Mean speed", "mean_speed_kmh", "km/h"],
                ["Completed trips", "total_completed_trips", "trips"],
              ] as const).map(([label, key, unit]) => <div className="summary-row" key={key}><span>{label}</span><b>{format(live?.results_summary.fixed?.[key], key === "total_completed_trips" ? 0 : 1)} <i>{unit}</i></b><b className="adaptive-value">{format(live?.results_summary.adaptive?.[key], key === "total_completed_trips" ? 0 : 1)} <i>{unit}</i></b></div>)}
            </div>
          </section>}
          {live?.status === "completed" && Object.keys(live.results_summary).length > 0 && <PerformanceInsights summary={live.results_summary} />}
          <div className="lower-grid">
            <div className="trend-grid">
              <Trend title="Queue length" samples={samples} fixedKey="fixed_queue" adaptiveKey="adaptive_queue" unit="vehicles" />
              <Trend title="Accumulated delay" samples={samples} fixedKey="fixed_delay" adaptiveKey="adaptive_delay" unit="vehicle-seconds" />
            </div>
            <section className="event-card panel">
              <div className="trend-title-row"><div><span className="section-kicker">ADAPTIVE CONTROLLER</span><h3>Decision log</h3></div><span className="live-tag"><i />LIVE</span></div>
              {events.length ? <ul className="event-list">{events.map((event, index) => <li key={`${event}-${index}`}>{event}</li>)}</ul> : <div className="chart-empty">Adaptive decisions will appear when SUMO records them.</div>}
            </section>
          </div>
          <div className="reference-grid">
            {siteGeometry && (
              <VectorMiniMap geometry={siteGeometry} vehicles={(mode === "fixed" ? single : adaptive)?.vehicles ?? []} />
            )}
            <DetectorNetwork controller={mode === "fixed" ? single : adaptive} />
            <FleetMix controller={mode === "fixed" ? single : adaptive} />
            <TrafficAlerts controller={mode === "fixed" ? single : adaptive} />
            <RunHistory runs={runHistory} onClear={() => setRunHistory([])} />
          </div>
        </section>

        <aside className="metrics-panel panel">
          <div className="panel-heading"><div><span className="section-kicker">LIVE TELEMETRY</span><h2>Intersection metrics</h2></div><span className="live-tag"><i />LIVE</span></div>
          {mode === "compare" ? <>
            <Metric label="Vehicles active" fixed={fixedMetrics?.active_vehicles} adaptive={adaptiveMetrics?.active_vehicles} unit="veh" digits={0} />
            <Metric label="Mean wait" fixed={fixedMetrics?.average_wait_seconds} adaptive={adaptiveMetrics?.average_wait_seconds} unit="sec" />
            <Metric label="Queue now" fixed={fixedMetrics?.total_queue_vehicles} adaptive={adaptiveMetrics?.total_queue_vehicles} unit="veh" />
            <Metric label="Accumulated delay" fixed={fixedMetrics?.accumulated_delay_vehicle_seconds} adaptive={adaptiveMetrics?.accumulated_delay_vehicle_seconds} unit="veh·s" />
            <Metric label="Completed trips" fixed={fixedMetrics?.completed_vehicles} adaptive={adaptiveMetrics?.completed_vehicles} unit="trips" digits={0} />
          </> : <>
            <div className="single-metric"><span>Active vehicles</span><b>{singleMetrics?.active_vehicles ?? "—"}</b></div>
            <div className="single-metric"><span>Mean wait</span><b>{format(singleMetrics?.average_wait_seconds)} sec</b></div>
            <div className="single-metric"><span>Queue now</span><b>{format(singleMetrics?.total_queue_vehicles)} veh</b></div>
            <div className="single-metric"><span>Accumulated delay</span><b>{format(singleMetrics?.accumulated_delay_vehicle_seconds)} veh·s</b></div>
            <div className="single-metric"><span>Completed trips</span><b>{singleMetrics?.completed_vehicles ?? "—"}</b></div>
          </>}
          <div className="approach-section"><div className="approach-heading"><span className="section-kicker">QUEUE BY APPROACH</span>{mode === "compare" && <span className="approach-legend"><i className="legend-fixed" /> Fixed <i className="legend-adaptive" /> Adaptive</span>}</div>
            {["North", "South", "East", "West"].map((direction) => <div className={`approach-row ${mode !== "compare" ? "single-approach-row" : ""}`} key={direction}><span>{direction}</span>{mode === "compare" ? <><b>{format(fixedMetrics?.queues_by_approach[direction], 0)}</b><b className="adaptive-value">{format(adaptiveMetrics?.queues_by_approach[direction], 0)}</b></> : <b>{format(singleMetrics?.queues_by_approach[direction], 0)} veh</b>}</div>)}
          </div>
          {mode === "compare" ? <Metric label="Mean speed" fixed={fixedMetrics?.average_speed_mps} adaptive={adaptiveMetrics?.average_speed_mps} unit="m/s" /> : <div className="single-metric"><span>Mean speed</span><b>{format(singleMetrics?.average_speed_mps)} m/s</b></div>}
          {mode === "compare" ? <Metric label="Mean trip travel" fixed={fixedMetrics?.average_completed_trip_travel_time_seconds} adaptive={adaptiveMetrics?.average_completed_trip_travel_time_seconds} unit="sec" /> : <div className="single-metric"><span>Mean trip travel</span><b>{format(singleMetrics?.average_completed_trip_travel_time_seconds)} sec</b></div>}
          <SignalPlan controller={mode === "fixed" ? single : adaptive ?? single} />
          <div className="solver-card"><span className="section-kicker">LAST SOLVER RESULT</span>{adaptive?.solver ? <><b>{adaptive.solver.solver} · {adaptive.solver.converged ? "converged" : "fallback"}</b><span>{adaptive.solver.status}</span><small>NS {format(adaptive.solver.green_seconds[0])}s · EW {format(adaptive.solver.green_seconds[1])}s</small></> : <span className="solver-empty">No optimizer decision reported yet.</span>}
            {adaptive?.flow_estimation && <details className="flow-details"><summary>Arrival flow · {adaptive.flow_estimation.used ? "used" : "diagnostic"}</summary>
              <span>{adaptive.flow_estimation.method} · {adaptive.flow_estimation.status} · rank {adaptive.flow_estimation.rank}</span>
              <div className="flow-equation">{adaptive.flow_estimation.matrix ? <span>A = [{adaptive.flow_estimation.matrix.map((row) => row.map((value) => format(value, 2)).join("  ")).join("; ")}]</span> : <span>No detector matrix for this interval</span>}<span>b = [{adaptive.flow_estimation.rhs.map((value) => format(value, 3)).join(", ")}] veh/s</span>{adaptive.flow_estimation.solution && <span>x = [{adaptive.flow_estimation.solution.map((value) => format(value, 3)).join(", ")}] veh/s</span>}</div>
              {adaptive.flow_estimation.row_operations.length > 0 && <ol>{adaptive.flow_estimation.row_operations.map((operation, index) => <li key={`${operation}-${index}`}>{operation}</li>)}</ol>}
              {adaptive.flow_estimation.residual !== null && <small>Residual {format(adaptive.flow_estimation.residual, 6)}</small>}
            </details>}
          </div>
          <div className="export-row"><button onClick={exportCsv} disabled={!hasSamples} title={hasSamples ? "Download observed telemetry as CSV" : "CSV export is available after the first telemetry sample"}><Download size={14} />CSV</button><button onClick={exportJson} title="Download current state and observed history as JSON"><Download size={14} />JSON</button></div>
        </aside>
      </main>

      <footer className="app-footer">
        <div className="app-footer-content">
          <span>Map data <strong>© OpenStreetMap contributors</strong> (ODbL 1.0)</span>
          <span className="footer-sep">·</span>
          <span>Simulation on real road geometry with assumed demand</span>
          <span className="footer-sep">·</span>
          <button type="button" className="footer-link-button" onClick={() => setProvenanceOpen(true)}>
            View Provenance Tags
          </button>
        </div>
      </footer>

      <RealVsAssumedPanel isOpen={provenanceOpen} onClose={() => setProvenanceOpen(false)} geometry={siteGeometry} />
    </div>
  );
}
