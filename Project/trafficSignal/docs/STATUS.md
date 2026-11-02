# Traffic Signal Platform v4 — Stage 0 audit

Audit date: 2026-10-26 (Asia/Kolkata)  
Source revision: `e78083cd90b1a72f682bd754fd6680b3e796c010` (working tree contains changes)  
SUMO: Eclipse SUMO 1.28.0  
Project root: `Project/trafficSignal/`

## Stage 0 gate

| Check | Result | Evidence | Risk / limitation |
|---|---|---|---|
| Backend and integration tests | Pass | Re-run `PYTHONPATH=. /Users/adityakumar/Documents/VSCODE/.venv/bin/pytest Project/trafficSignal/tests -q` → 40 passed in 9.36 s with local TraCI access. API tests include Vite fallback-port CORS preflight and reject an external origin. | Tests cover the existing two-phase signal model, not the proposed 4-phase/protected-left suite or property-based invariants. |
| Frontend production build | Pass | Re-run `npm run build` in `web/` after the scene changes → Vite build succeeded. | Three.js vendor chunk is now 557.32 kB minified; Vite reports the >500 kB chunk warning. |
| API server | Running | Baseline API on 8001 returned HTTP 200. A fresh API with the CORS fix on 8002 passed the full UI workflow. | Custom ports are used because the standard ports were occupied. |
| Browser server | Running | Baseline Vite at 5175 and fresh Vite at 5176 returned HTTP 200. | 5175/5176 are Vite fallback ports; both are covered by the loopback-only CORS regex. |
| Current 1440×900 and 1920×1080 captures | Done | Fresh Playwright/Brave screenshots in `docs/visual/baseline/`; each has `document.visibilityState="visible"`, paused seed-42 rush-hour SUMO state, 102 vehicles per controller, and visible 3D vehicle meshes. | Browser is headless, though its ANGLE renderer is Apple Metal. Not a headed-user-session capture. |
| Renderer statistics | Done | Per-scene `renderer.info` is recorded at both viewports in `docs/visual/baseline/performance-baseline.json`; 1440: 121 calls / 48,026 triangles; 1920: 124 calls / 48,214 triangles. | These are current-frame renderer counts; memory readings are browser JavaScript heap only. |
| Frame-time percentiles and memory | Initial baseline done; shared-renderer capture done | Initial two-renderer baseline: 1440 p50/p95/p99 16.7/25.6/31.5 ms; 1920 16.7/24.9/30.8 ms. New one-renderer 10-second windows: 1440 16.7/16.7/16.8 ms; 1920 16.7/16.8/16.8 ms. JS heap was 32.7 MB and 42.7 MB in the new capture. | The shared-renderer sample meets the 55 FPS p95 target in both viewports; the initial baseline does not. These are headless runs. Process/GPU memory is not measured. |
| GPU identification | Partial | WebGL reports `ANGLE (Apple, ANGLE Metal Renderer: Apple M5, Unspecified Version)`; system query reports Apple M5, 8 GPU cores. | Exact Mac model and thermal state are unknown; results are not a MacBook Air hardware certification. |

**Gate status: passed.** Backend tests and the frontend build pass, both servers respond, and the requested screenshots, renderer counters, frame-time percentiles, and JavaScript heap readings are recorded. The initial two-renderer baseline p95 was 24.9–25.6 ms; the shared-renderer follow-up measured 16.7–16.8 ms across both viewports. Hardware-model, process/GPU memory, and headed-browser measurements remain limitations.

## Track A — 3D visual audit

| ID | Status | Evidence | Risk / gap |
|---|---|---|---|
| V1 Rendering foundation | Partial | `trafficScene.ts` now has sRGB/ACES output, a generated local RoomEnvironment PMREM, warm-neutral key and hemisphere fill, a tighter shadow frustum, instanced soft contact shadows, and locally generated asphalt albedo/roughness/normal textures. | GTAO/SSAO, bloom, SMAA, independent effect toggles, and shadow-acne/aliasing scorecard remain. |
| V2 Smooth motion | Partial | `vehicleInterpolation.js` uses a speed-scaled 150 ms Hermite buffer, shortest-path heading interpolation, pause/resume handling, and rollback/spawn/despawn behavior. Twelve assertions and the expanded Playwright pause/resume review pass. Latest 15-second run at 197/194 vehicles measured a 0.039 m mean and 0.108 m p95 adaptive displacement-prediction residual in `docs/visual/v1-pbr/auto-resolution-high-load/`. | Residual is against the previous speed/heading prediction, not ground truth. Need turning-path visual critique and a showcase clip before claiming no visible jitter. |
| V3 Vehicles | Partial | Instanced procedural bodies now use beveled rounded boxes; per-vehicle lamps render, and brake-lamp brightness follows real SUMO speed. Backend still uses six seeded vehicle types. | Need nine classes, a catalog, wheel rotation/steer/body dynamics, vehicle-signal/route-based lamps, and LOD. |
| V4 Road and junction realism | Partial | Locally generated asphalt albedo/roughness/normal maps include subtle tire-wear tracks; existing road markings, crossings, signals, and procedural buildings remain live/illustrative. | No cracks/patches, bevelled curbs, drains/manholes, or verified curved junction corners. |
| V5 Surroundings | Partial | Scene includes procedural buildings and instanced-looking tree props. | Limited facade/height variation and no surveyed skyline, shopfronts, shelters, benches, bins, lamps, or prop-budget evidence. |
| V6 Signals and overlays | Partial | Live signal phase and aggregate approach queue/wait overlays are rendered from API state; detector counts/rates appear in the dashboard. | No per-lane queue heat, selected-vehicle inspection/trail, flow arrows, color-blind shape cues, overlay toggles, or phase-change pulse. |
| V7 Cameras | Partial | `OrbitControls` plus synchronized overview, top-down analytic, and street-level presets with 650 ms eased transitions. The expanded Brave browser review selected views from both comparison panels and confirmed two-way synchronization. | No vehicle-follow/hero intro, camera bounds, or showcase orbit. |
| V8 Time of day and weather | Missing | No scene time/weather controls found. | Cosmetic weather, lighting, and wet-road variation are absent. |
| V9 Performance architecture | Partial | Compare mode uses one shared WebGLRenderer and two scissor viewports. Four quality tiers and opt-in/out adaptive DPR are implemented. A controlled pressure test drove scale 1.0→0.9 and recovery to 0.95 with zero browser errors; see `docs/visual/v1-pbr/dynamic-resolution/`. The High 2560×1440/15s run reached 197/194 vehicles, 16.65 ms mean, 16.7 ms p95, 16.8 ms p99, 294 calls, 638,822 triangles, 14 textures, and 37.3 MB JS heap. The in-app report and hidden-tab pause are validated. | Headless on an unidentified Mac M5 host, not MacBook Air certification. Repeated alternating renderer runs, GPU/process memory, and automatic quality degradation beyond DPR remain. |
| V10 Visual QA and regression | Partial | The expanded Brave browser audit exercises start/demo, pause/resume/stop/reset, CSV/JSON and performance downloads, docs link, run-history select/export/clear, error dismissal, reconnect after a simulated WebSocket drop, synchronized camera presets, and CSV disabled/enabled states. It passed with zero unexpected console errors; the only 409 was the deliberate error-state check. Scroll-reset 1440×900 and 1920×1080 captures and a round 1 manual scorecard are in `docs/visual/v1-pbr/camera-review/` and `docs/visual/scorecard-round-1.md`. | No pixel-diff suite/tolerance, before-after contact sheet, or three critique rounds. A scene-only showcase image/video is still missing. |

## Track B — evidence and control audit

| ID | Status | Evidence | Risk / gap |
|---|---|---|---|
| F1 Statistical benchmark | Partial | `results/` contains seed/scenario comparison CSV/JSON files; `README.md` records seed-dependent wins and losses. | Not 20+ seeds × 4 scenarios × 30+ minutes; no paired confidence intervals, significance tests, complete metric win rates, manifests, or one-command statistical report. |
| F2 Demand sweep | Missing | No demand-sweep runner/report found. | Controller trade-offs across load levels are unknown. |
| F3 Controller suite | Partial | Backend has fixed-time and adaptive control; `optimizer.py` includes Webster initialization and SLSQP/PGD optimization. | No SUMO-actuated, Max-Pressure, gap-out, or protected-left 4-phase plan. |
| F4 Safety monitor and properties | Partial | `tests/test_signal_safety.py` contains deterministic safety checks; clearance phases are represented in the SUMO program and controller logic. | No Hypothesis property suite or runtime safety monitor audit across every transition. |
| F5 Detector robustness | Partial | Adaptive estimation has Gauss–Jordan rank/status and nonnegative/plausibility checks with fallback, covered by `test_adaptive_estimation.py`. | No injected noise, dropout, or detector-failure scenario suite. |

## Track C — extras audit

| ID | Status | Evidence | Risk / gap |
|---|---|---|---|
| F6 RL controller | Missing | No RL policy or training/evaluation code found. | Not available. |
| F7 Parameter tuning splits | Missing | No train/validation/test tuning pipeline found. | Not available. |
| F8 Numerical methods and forecasts | Partial | Existing trapezoidal integration, Richardson error, OLS/Gauss–Jordan, Webster, PGD, and SLSQP are documented in `README.md`. | Jacobi, Gauss–Seidel comparison, RK4 fluid model, and EWMA/Kalman forecasting absent. |
| F9 Explainability | Partial | Browser decision log and detector-flow solver/equation details exist in `web/src/App.tsx`. | No unified explanation of safety overrides and measured controller trade-offs. |
| F10 Offline OSM import | Missing | No OSM importer found. | Not available. |
| F11 Real-count CSV / GEH | Missing | No calibration CSV import or GEH calculation found. | Not available. |
| F12 Mixed traffic / people / preemption / incidents | Partial | Six SUMO vehicle classes are present. | No SUMO pedestrian data, ambulance preemption, lane closure, or incident workflow. |
| F13 Recording, replay, PDF | Missing | `ARCHITECTURE.md` explicitly says replay is not implemented. | Not available. |
| F14 Beat-the-algorithm mode | Missing | No interactive challenge mode found. | Not available. |
| F15 Presentation mode / language toggle | Missing | No presentation mode or English/Hindi toggle found. | Not available. |
| F16 SQLite run database | Missing | Browser retains a small localStorage run history; backend exports CSV/JSON. | No durable queryable SQLite run store. |
| F17 One-command start / containers / CI / health / metrics | Partial | `/health` exists and returns `{"status":"ok"}`; README documents separate API and Vite launch commands. | No one-command launcher, Docker, CI workflow, or `/metrics` endpoint. |

## Baseline artifacts found

| File | Dimensions | State | Note |
|---|---:|---|---|
| `docs/visual/baseline/dashboard-1440x900.png` | 1440×900 | Fresh | Playwright/Brave, visible document, seed 42, rush-hour, 7,200 veh/h per axis, paused at sim time 46 s, 102 vehicles per controller. |
| `docs/visual/baseline/dashboard-1920x1080.png` | 1920×1080 | Fresh | Same paused run/state and visible vehicles as 1440×900. |
| `docs/visual/baseline/performance-baseline.json` | JSON | Fresh Stage 0 measurements | Renderer counters, 10-second p50/p95/p99 frame-time windows, JS heap, Apple Metal GPU identity, and browser errors. |
| `docs/visual/after/motion-performance-report.json` | JSON | Two-canvas comparison measurement | High quality at 2560×1440 with 197–201 live vehicles per scene, frame-time percentiles, JS heap, and interpolation residual trace. |
| `docs/visual/after/frame-position-error.svg` | SVG | Fresh Stage A plot | Per-frame mean displacement prediction residual across vehicles present in adjacent render frames. |
| `docs/visual/after/dashboard-motion-2560x1440.png` | 2560×1440 | Fresh Stage A capture | Live 8× rush-hour simulation at High quality; 201 fixed and 197 adaptive vehicles in the captured frame. |
| `docs/visual/scissor-candidate/motion-performance-report.json` | JSON | Shared-renderer candidate | 15-second High run at 2560×1440, 196 vehicles per scene; combined renderer counters and per-view frame-time samples. |
| `docs/visual/scissor-candidate/dashboard-motion-2560x1440.png` | 2560×1440 | Shared-renderer candidate | Visible live comparison capture; the full UI review passed with no browser errors. |
| `docs/visual/scissor-candidate/stage0/performance-baseline.json` | JSON | Shared-renderer viewport check | One-renderer comparison at 1440×900 and 1920×1080; 10-second p95 was 16.7 and 16.8 ms with zero page errors or failed responses. |
| `docs/visual/scissor-candidate/ui-review/traffic_performance_medium_1793010637700.json` | JSON | In-app report export | Playwright-downloaded report validated for live fixed/adaptive diagnostics, GPU identity, draw calls, triangles, and frame-time percentiles. |
| `docs/visual/renderer-comparison/shared-scissor-run2/motion-performance-report.json` | JSON | Second shared-renderer sample | 15-second High run at 2560×1440, 201/197 vehicles, matching the former two-canvas run's load. |
| `docs/visual/v1-pbr/auto-resolution-high-load/motion-performance-report.json` | JSON | PBR/automatic-DPR high-load run | High tier, 2560×1440, 197/194 live vehicles, mean 16.65 ms, p95 16.7 ms, p99 16.8 ms; motion residual is a prediction diagnostic, not ground truth. |
| `docs/visual/v1-pbr/dynamic-resolution/dynamic-resolution-report.json` | JSON | Adaptive-resolution pressure/recovery test | Scale changed 1.0→0.9 under injected main-thread pressure and recovered to 0.95; no browser errors. |
| `docs/visual/v1-pbr/camera-review/dashboard-1440x900.png` | 1440×900 | Current PBR UI review | Scroll-reset light neutral dashboard with the complete junction in both comparison viewports and live SUMO vehicles. |
| `docs/visual/v1-pbr/camera-review/dashboard-1920x1080.png` | 1920×1080 | Current PBR UI review | Second scroll-reset comparison capture; the same review also checks the synchronized camera presets and full button/error/reconnect workflow. |
| `docs/visual/v1-pbr/camera-review/traffic_performance_medium_1793013515956.json` | JSON | Expanded Brave UI review | Existing action/error/reconnect/export flow, synchronized overview/analytic/street selection, and CSV enable/disable behavior; zero unexpected page/console errors. |
| `docs/visual/scorecard-round-1.md` | Markdown | Manual visual critique | Scores the clean dashboard/scene capture and records follow-up actions; no automated pixel score claimed. |
| `docs/screenshots/dashboard-1440x900.png` | 1440×900 | Existing, stale | Earlier paused run and dark UI; retained as historical artifact. |
| `docs/screenshots/dashboard-1920x1080.png` | 1920×1080 | Existing, stale | Earlier visual-review capture. |
| `docs/screenshots/dashboard-live-insights.png` | 1920×1080 | Existing, stale | Earlier live-insights capture. |

No `reference/` directory exists under the project. The requested art direction is recorded in `docs/visual-spec.md`; no external artwork or vehicle assets are currently used.
