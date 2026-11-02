import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { createSharedTrafficRenderer, createTrafficScene, type CameraPreset, type ControllerLiveState, type RenderQuality, type SceneDiagnostics, type SharedTrafficRenderer } from "./trafficScene";

const SharedRendererContext = createContext<SharedTrafficRenderer | null>(null);

type SharedGridProps = { quality: RenderQuality; adaptiveResolution: boolean; children: ReactNode };

export function SharedTrafficSceneGrid({ quality, adaptiveResolution, children }: SharedGridProps) {
  const root = useRef<HTMLDivElement>(null);
  const [renderer, setRenderer] = useState<SharedTrafficRenderer | null>(null);

  useEffect(() => {
    if (!root.current) return;
    const shared = createSharedTrafficRenderer(root.current, quality);
    setRenderer(shared);
    return () => shared.dispose();
  }, [quality]);

  useEffect(() => {
    renderer?.setAdaptiveResolution(adaptiveResolution);
  }, [adaptiveResolution, renderer]);

  return <SharedRendererContext.Provider value={renderer}>
    <div className="scene-grid shared-renderer" ref={root}>
      {renderer ? children : <div className="scene-loading shared-scene-loading">Preparing shared traffic renderer…</div>}
    </div>
  </SharedRendererContext.Provider>;
}

import type { SiteGeometry } from "./types";

declare global {
  interface Window {
    __trafficSceneDiagnostics?: Record<string, (resetWindow?: boolean) => SceneDiagnostics | null>;
  }
}

type Props = {
  label: string;
  snapshot: ControllerLiveState | null;
  quality: RenderQuality;
  adaptiveResolution: boolean;
  simulationTime: number | null;
  speed: number;
  status: string;
  cameraPreset: CameraPreset;
  siteGeometry?: SiteGeometry | null;
};

export function TrafficScene({ label, snapshot, quality, adaptiveResolution, simulationTime, speed, status, cameraPreset, siteGeometry }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const scene = useRef<ReturnType<typeof createTrafficScene> | null>(null);
  const sharedRenderer = useContext(SharedRendererContext);

  useEffect(() => {
    if (!host.current) return;
    scene.current = createTrafficScene(host.current, quality, sharedRenderer ?? undefined, siteGeometry);
    window.__trafficSceneDiagnostics ??= {};
    window.__trafficSceneDiagnostics[label] = (resetWindow = false) => scene.current?.getPerformanceSnapshot(resetWindow) ?? null;
    return () => {
      if (window.__trafficSceneDiagnostics) delete window.__trafficSceneDiagnostics[label];
      scene.current?.dispose();
      scene.current = null;
    };
  }, [label, quality, sharedRenderer, siteGeometry]);

  useEffect(() => {
    scene.current?.setAdaptiveResolution(adaptiveResolution);
  }, [adaptiveResolution, sharedRenderer]);

  useEffect(() => {
    scene.current?.setCameraPreset(cameraPreset);
  }, [cameraPreset]);

  useEffect(() => {
    scene.current?.update(snapshot, simulationTime, speed, status);
  }, [snapshot, simulationTime, speed, status]);

  const phase = snapshot?.signal?.phase;
  const signalLabel = phase === 0 || phase === 3 ? "Green" : phase === 1 || phase === 4 ? "Yellow" : phase === 2 || phase === 5 ? "All red" : "Waiting for signal";

  return (
    <section className="scene-card" aria-label={`${label} traffic view`}>
      <div className="scene-heading">
        <div>
          <span className="scene-kicker">LIVE SIMULATION</span>
          <h2>{label}</h2>
        </div>
        <div className="scene-heading-actions">
        <label className="camera-preset-control"><span className="sr-only">Camera view for {label}</span><select aria-label={`Camera view for ${label}`} value={cameraPreset} onChange={(event) => window.dispatchEvent(new CustomEvent("traffic-camera-preset", { detail: event.target.value as CameraPreset }))}><option value="overview">Overview</option><option value="analytic">Analytic</option><option value="street">Street level</option></select></label>
        <div className="phase-chip">
          <span className={`phase-dot phase-${signalLabel.toLowerCase().replaceAll(" ", "-")}`} />
          {signalLabel}
          {phase !== undefined && phase !== null && <span className="phase-number">P{phase}</span>}
        </div>
        </div>
      </div>
      <div className="scene-host" ref={host} />
      {snapshot?.metrics && <div className="queue-overlay" role="group" aria-label={`${label} approach queues and mean wait`}>
        <dl>{(["North", "East", "South", "West"] as const).map((direction) => <div key={direction}><dt>{direction}</dt><dd>{Math.round(snapshot.metrics.queues_by_approach[direction] ?? 0)} veh</dd></div>)}
          <div className="wait-readout"><dt>Mean wait</dt><dd>{snapshot.metrics.average_wait_seconds.toFixed(1)}s</dd></div>
        </dl>
      </div>}
      <div className="scene-footer">
        <span>{snapshot ? `${snapshot.vehicles.length} active vehicles` : "Waiting for SUMO state"}{snapshot?.signal?.green_seconds_remaining !== null && snapshot?.signal?.green_seconds_remaining !== undefined && ` · ${snapshot.signal.green_seconds_remaining.toFixed(0)}s green remaining`}</span>
        <span>Drag to orbit · scroll to zoom</span>
      </div>
    </section>
  );
}
