# Adaptive Traffic Signal Optimization Simulator
### B.Tech Major Project in Numerical Analysis & Intelligent Transportation Systems

An end-to-end Python desktop application that connects **Eclipse SUMO** (Simulation of Urban MObility) with constrained numerical optimization and numerical integration algorithms to optimize traffic signal timings and mitigate urban congestion.

The simulator performs fair, scientific A/B benchmarking between:
1. **Fixed-Time Signal Control** (Baseline standard cyclic schedule)
2. **Adaptive Signal Optimization** (Proposed constrained numerical optimization)

Both controllers operate under **strictly identical conditions**: identical road network geometry, identical vehicle demand profiles, identical simulation duration, and identical pseudo-random arrival seeds (`seed=42`).

---

## 1. Mathematical Formulations & Numerical Methods

### 1.1 Discrete-Time Queue Evolution Model
Each approach lane group $i$ is modeled via the conservation law:
$$q_i(k+1) = \max\left(0, \min(C_{\text{storage}}, q_i(k) + a_i(k) - d_i(k))\right)$$
where:
- $q_i(k)$ is the queue length at discrete step $k$ (vehicles).
- $a_i(k) = \lambda_i(k) \Delta t$ is the arrival count over interval $\Delta t = 1.0\text{ s}$.
- $d_i(k) = s_i \cdot \gamma_i(k) \Delta t$ is the departure capacity, where $s_i$ is the saturation flow rate ($\approx 0.50\text{ veh/s/lane} = 1800\text{ veh/h/lane}$) and $\gamma_i(k) \in \{0, 1\}$ indicates green phase status.

### 1.2 Composite Trapezoidal Rule for Accumulated Delay
Continuous vehicle delay is defined as the time integral of the queue trajectory:
$$D(T) = \int_0^T q(t) dt$$

Discretized numerically via the **Composite Trapezoidal Rule**:
$$\int_{t_0}^{t_N} q(t) dt \approx \sum_{k=0}^{N-1} \frac{q(t_k) + q(t_{k+1})}{2} (t_{k+1} - t_k)$$

#### Numerical Error Estimation (Richardson Extrapolation)
Because the composite trapezoidal rule has local truncation error $\mathcal{O}(h^2)$, the global truncation error is estimated dynamically using step-halving:
$$E_T \approx \frac{|I_h - I_{2h}|}{3}$$
This truncation error is recorded and reported in the exported CSV metrics.

### 1.3 Least-Squares Parameter Estimation (OLS)
When empirical discharge data is sampled, the effective saturation flow rate $s$ and lost time offset $\beta_0$ are estimated via Ordinary Least Squares:
$$\min_{s, \beta_0} \sum_{j=1}^M \left( \Delta q_j - (\beta_0 + s \cdot t_j) \right)^2$$
yielding normal equations with analytical standard error, residuals, and coefficient of determination $R^2$.

### 1.4 Constrained Signal Optimization Formulation
At each decision epoch, the controller solves the non-linear constrained optimization problem:
$$\min_{\{g_1, \dots, g_M\}} J(g) = \sum_{m=1}^M w_m \int_0^C q_m(t; g_m) dt$$
subject to:
$$g_{m, \min} \le g_m \le g_{m, \max} \quad \forall m \in \{1, \dots, M\}$$
$$\sum_{m=1}^M g_m = C - \sum_{m=1}^M (y_m + r_{\text{all}, m})$$
where:
- $g_m$: Green time allocated to phase $m$.
- $G_{\min} = 10.0\text{ s}$, $G_{\max} = 60.0\text{ s}$.
- Yellow clearance $y_m = 4.0\text{ s}$, All-Red clearance $r_{\text{all}, m} = 2.0\text{ s}$.
- Total lost time $L = \sum (y_m + r_{\text{all}, m}) = 12.0\text{ s}$ per 90s cycle.

#### Numerical Solvers Implemented:
1. **SciPy SLSQP** (Sequential Least Squares Programming) with active box bounds and linear hyperplane equality constraints.
2. **Projected Gradient Descent (PGD)** with exact projection onto the canonical simplex with box bounds:
   $$g^{(k+1)} = \Pi_{\mathcal{S}} \left( g^{(k)} - \alpha \nabla J(g^{(k)}) \right)$$
   using Lagrange multiplier bisection for Karush-Kuhn-Tucker (KKT) optimality.
3. **Webster Equisaturation Model** (Analytical baseline):
   $$g_m = \frac{y_m}{Y} (C - L) \quad \text{where } y_m = \frac{v_m}{s_m}, Y = \sum y_m$$

### 1.5 Safety & Non-Conflicting Signal Invariants
- **Phase Separation**: Conflicting arterial (North-South) and collector (East-West) traffic never receive green simultaneously.
- **Fail-Safe Fallback**: If numerical optimization encounters degenerate matrices or divergence, the system automatically falls back to the validated Webster timing plan with zero simulation interruption.

---

## 2. Project Architecture

```
Project/trafficSignal/
├── main.py                     # Master launcher (GUI desktop or CLI benchmark)
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & mathematical report
├── config/
│   ├── __init__.py
│   └── settings.py             # Global constants & SUMO binary auto-detection
├── backend/
│   ├── __init__.py
│   ├── numerical_methods.py    # Trapezoidal integration, Richardson error, OLS, PGD
│   ├── traffic_model.py        # Discrete-time queue evolution & movement states
│   ├── optimizer.py            # SLSQP & PGD constrained optimization + Webster split
│   ├── simulation.py           # TraCI bridge, FixedTimeController & AdaptiveController
│   ├── metrics.py              # Telemetry logger, statistical summary & CSV exporter
│   └── data_loader.py          # Programmatic SUMO scenario generator (net, rou, det, sumocfg)
├── frontend/
│   ├── __init__.py
│   ├── app.py                  # Main CustomTkinter desktop window
│   ├── dashboard.py            # Control panel, KPI cards, sliders & status console
│   └── charts.py               # Embedded Matplotlib canvas (queue & delay curves)
├── data/
│   └── networks/               # Compiled SUMO XML scenario files
├── results/                    # Exported comparison CSVs & telemetry data
└── tests/
    ├── __init__.py
    ├── test_numerical_methods.py # 7 tests (trapezoidal, OLS, PGD simplex)
    ├── test_traffic_model.py     # 3 tests (queue conservation, spillback)
    ├── test_optimizer.py         # 3 tests (Webster, SLSQP bounds, fallback)
    └── test_simulation.py        # 3 tests (scenario builder, headless TraCI runs)
```

---

## 3. Installation & Setup (macOS / VS Code)

### Prerequisites
- macOS (Apple Silicon or Intel) with Python 3.10+
- VS Code

### Setup Virtual Environment
```bash
cd /Users/adityakumar/Documents/VSCODE
source .venv/bin/activate
pip install -r Project/trafficSignal/requirements.txt
```

*Note: `eclipse-sumo` pre-compiled arm64 binaries (including `sumo`, `sumo-gui`, and `netconvert`) are bundled in the virtual environment.*

---

## 4. Running the Application

### OpenStreetMap site data status

A provisional Boring Road area extract is cached at [`data/sites/boring_road_patna_2026-10-28.osm`](data/sites/boring_road_patna_2026-10-28.osm), with a tile-free vector preview at [`docs/sites/boring_road_patna.svg`](docs/sites/boring_road_patna.svg). The mapped fountain point is a candidate center, not a verified island boundary or a confirmed junction name. This data is not yet a running Patna scenario: the current simulator remains the default synthetic four-way, and no Patna demand counts have been supplied. Any future site run must be labeled **“Simulation on real road geometry with assumed demand”** unless calibrated counts are provided.

Map data is from OpenStreetMap and is available under ODbL 1.0. © OpenStreetMap contributors. No third-party map tiles, aerial imagery, or Street View are used.

### Option A: Launch the Desktop GUI Dashboard
```bash
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py
```
**Features in GUI**:
- **Simulation Mode**: Choose *Head-to-Head Comparative Benchmark*, *Adaptive Optimization*, or *Fixed-Time Baseline*. The comparison launches two synchronized SUMO simulations using the same seed and generated route schedule.
- **Launch SUMO-GUI Animation**: Check the checkbox to see the SUMO network, vehicles, and signals in SUMO-GUI's 2D simulation view.
- **Interactive Controls**: Start, Pause, Resume, Stop, Reset; Space toggles pause/resume and R resets the view.
- **Real-Time Embedded Charts**: Fixed and adaptive queue/delay curves update together from live telemetry during paired comparison.
- **Browser 3D fleet**: The browser scene renders live SUMO vehicle positions using six seeded classes: hatchback, sedan, SUV, van, bus, and truck.
- **Live diagnostics and run summary**: Scene overlays show approach queues, mean wait, and green countdowns. The adaptive solver panel exposes detector flow equations and Gauss–Jordan row operations; completed runs show fixed/adaptive queue, delay, wait, speed, throughput, and mean completed-trip travel time.
- **Export Results**: Save telemetry as CSV and benchmark results as both CSV and JSON. Each comparison record includes scenario settings, fixed/adaptive metrics, percentage changes, and adaptive decisions.
- **Disconnected state**: SUMO startup or runtime failures are surfaced in the dashboard status badge and log.

### Option B: Run Automated CLI Benchmark (Headless)
Run a direct, reproducible comparison in the terminal:
```bash
# 120-second run with Peak traffic
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py --cli --duration 120 --demand Peak

# 180-second run with Medium traffic
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py --cli --duration 180 --demand Medium

# Launch with visual SUMO-GUI
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py --cli --duration 120 --demand Peak --gui

# Run a reproducible rush-hour profile
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py --cli --duration 180 --scenario rush_hour

# Repeat the same scenario with a different reproducible arrival schedule
PYTHONPATH=. .venv/bin/python3 Project/trafficSignal/main.py --cli --duration 120 --scenario balanced --seed 99
```

The GUI provides four seeded arrival patterns: Balanced, Heavy North–South, Sudden Surge, and Rush Hour. CLI options are `balanced`, `heavy_ns`, `sudden_surge`, and `rush_hour`. Arrival times are generated from a seeded Poisson process. Each comparison uses the same generated route file conditions for both controllers.

### Option C: Run Unit & Integration Test Suite
```bash
PYTHONPATH=. .venv/bin/pytest Project/trafficSignal/tests -v
```
**Latest verified test result**: 42 passed in 9.51 s, including offline tests for the cached OSM site data. SUMO integration cases require local loopback access for TraCI.

### Option D: Run the HTTP and WebSocket API

```bash
PYTHONPATH=. .venv/bin/python3 -m Traffic.api --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the typed OpenAPI contract. The server exposes `GET /api/state`, `POST /api/simulation/start|pause|resume|stop|reset`, and `/ws/live` (10 updates per second). Before SUMO provides a sample, simulation time and controller metrics are `null`/empty; connection failures report `disconnected` with an error.

### Option E: Run the Browser Control Center

Start the API in one terminal and Vite in a second:

```bash
PYTHONPATH=. .venv/bin/python3 -m Traffic.api --host 127.0.0.1 --port 8000
npm --prefix Project/trafficSignal/web run dev
```

Open `http://127.0.0.1:5173`. The browser dashboard visualizes live SUMO vehicles and signals in a procedural Three.js intersection, supports fixed/adaptive comparison, offers paced simulation speed from 0.5× to 8×, and exports sampled telemetry as CSV or JSON. Set separate north–south and east–west demand rates (0–7,200 vehicles/hour) before a run. Completed comparisons show measured adaptive-versus-fixed changes in mean wait, accumulated delay, and completed trips. The latest eight completed run summaries are saved in browser storage for review and JSON export. Use **Try a 60-second demo** for a one-click comparison with balanced demand and seed 42. Scenario descriptions, run progress, and duration/seed guidance are shown beside the controls. The 1-second simulation timestep is paced against wall time for browser runs; CLI and desktop benchmark execution remains unpaced. For a production frontend build, run `npm --prefix Project/trafficSignal/web run build`.

For the Playwright UI review, use `npm --prefix Project/trafficSignal/web run visual-review` with both servers running. To capture the Stage 0 high-demand screenshots, renderer counters, frame-time percentiles, and JavaScript heap at 1440×900 and 1920×1080, use `npm --prefix Project/trafficSignal/web run stage0-baseline`. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` if Playwright's bundled browser is unavailable. Fresh baseline artifacts are in [`docs/visual/baseline/`](docs/visual/baseline/); [`docs/screenshots/`](docs/screenshots/) retains earlier captures.

The latest UI uses one shared WebGL renderer with scissor rectangles for the fixed/adaptive comparison. Two High-tier 2560×1440, 15-second captures measured 16.66 ms mean, 16.7 ms p95, and 16.8 ms p99 at 196/196 and 201/197 vehicles. A prior two-canvas run at 201/197 measured the same mean, 24.3 ms p95, and 28.7 ms p99. The repeated candidate samples suggest fewer frame-time outliers, though a randomized controlled benchmark is still needed. A 10-second viewport capture also measured p95 of 16.7 ms at 1440×900 and 16.8 ms at 1920×1080, meeting the sampled 55 FPS frame-time target at both sizes. The 40 FPS 1% low threshold is met in the high-demand samples. The position residual plot is in `docs/visual/scissor-candidate/`; process/GPU memory and exact Mac model remain unverified. See [`docs/STATUS.md`](docs/STATUS.md) and [`docs/visual/baseline/performance-baseline.json`](docs/visual/baseline/performance-baseline.json).

The current scene adds a generated local PBR environment, warm-neutral lighting, soft instanced contact shadows, procedural asphalt albedo/roughness/normal maps, beveled vehicle bodies, and brake lamps driven by SUMO-reported speed. The camera selector offers synchronized overview, analytic top-down, and street-level views with eased transitions; OrbitControls remain available after each preset. Four quality tiers and optional adaptive render resolution are available. The high-load PBR/DPR report measured 16.65 ms mean and 16.7/16.8 ms p95/p99 at 197/194 vehicles. A separate pressure test drove resolution scale from 1.0 to 0.9 and gradual recovery to 0.95. These are headless Apple Metal measurements, not MacBook Air certification. The latest full browser review, including camera synchronization, existing button workflows, export, error dismissal, and reconnect checks, is recorded under [`docs/visual/v1-pbr/camera-review/`](docs/visual/v1-pbr/camera-review/).

Use the gauge icon in the dashboard header to download a browser-side Performance report JSON. It includes the active frame-time sample window, percentiles, renderer counters, GPU identity when exposed by the browser, viewport, and quality tier. In compare mode, draw-call and triangle counters are totals across both scissor-rendered scenes. A Playwright-validated example is [`traffic_performance_medium_1793010637700.json`](docs/visual/scissor-candidate/ui-review/traffic_performance_medium_1793010637700.json).

For how each supplied visual reference maps to real simulator data, see [`docs/REFERENCE_ANALYSIS.md`](docs/REFERENCE_ANALYSIS.md).

---

## 5. Experimental Results & Verification

Latest verified output from a 120-second balanced-scenario benchmark (seed 42, six-class fleet):
```
                         Fixed         Adaptive
Mean wait (s)            3.95           3.21
Total delay (veh·s)    812.0          711.0
Mean queue (vehicles)   6.79           5.95
Completed trips           31             32
```
Adaptive improved the listed metrics in this one seed-42 run. Other seeds include losses: balanced seed 1 had mean wait 2.71 s fixed vs 5.16 s adaptive, delay 659.5 vs 1051.5 veh·s, mean queue 5.53 vs 8.79, and trips 32 vs 25. The CSV reports percentage change vs fixed. Decision records include measured queue inputs, detector-derived phase flow rates, solver status, selected greens, and optimizer reason. The estimate is only used if the Gauss–Jordan result is unique, finite, nonnegative, and below the configured physical plausibility limit; the first decision falls back to configured demand because there is no detector interval yet. These results were regenerated after adding six seeded vehicle classes; earlier sedan-only measurements are not current.

Further implementation details and limitations are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and the five-minute walkthrough is in [`docs/DEMO.md`](docs/DEMO.md).
