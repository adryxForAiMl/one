# Boring Road Chauraha site module — audit and implementation plan

Status: Stage 0 audit and regression gate complete; Stage 1 OSM cache and preview generated; Stage 2 network/report generated but connectivity gate fails, so later stages are blocked. Site identity is provisional.  
Audit date: 2026-10-28.  
Stage 0 verification: `PYTHONPATH=. .venv/bin/pytest Project/trafficSignal/tests -q` from the workspace root passed **40 tests in 11.07 s** with local TraCI access. `npm --prefix Project/trafficSignal/web run build` succeeded; Vite still reports the existing 557.33 kB Three.js chunk warning.

## Existing four-way dependencies found

| Area | Current hardcoded dependency | Files |
|---|---|---|
| Network topology | `SumoNetworkBuilder` writes a centered, 4-arm, 2-lane-per-edge junction, fixed turn connections and a 12-link signal program into `intersection.*.xml`; detector IDs and lane names assume N/S/E/W arms. | `backend/data_loader.py`, generated `data/networks/intersection.{nod,edg,con,tll,det,net,rou}.xml`, `data/networks/simulation.sumocfg` |
| Routes and demand | Twelve named turning routes and a two-axis NS/EW demand profile are created from a seeded synthetic arrival process. | `backend/data_loader.py`, `config/settings.py` (`DemandProfile`) |
| Signal control | Controller defaults to `junction_center`; fixed phase schedule, adaptive two-phase split, detector aggregation, and queue interpretation all assume NS and EW pairs. | `backend/simulation.py`, `backend/optimizer.py`, `backend/traffic_model.py`, `backend/metrics.py`, `config/settings.py` |
| API state | Run request has scenario/mode/demand/timing but no site selector; state exposes four named approach queues and one signal phase integer. The manager always launches the existing builder/runner. | `api.py` (request/state models, snapshot serializers, `SimulationManager.start`, routes) |
| Scene geometry | Road, lane marks, crossing, signals, building context and center are procedural; signals are placed at four fixed coordinates and phase decoding is tied to current phase indices. Vehicle positions use a fixed world scale. | `web/src/trafficScene.ts`, `web/src/TrafficSceneView.tsx` |
| Dashboard | Scenario controls collect only NS/EW demand; detector, queue, comparison, and signal-plan views assume four cardinal approaches. No site metadata, attribution, or source/assumption panel exists. | `web/src/App.tsx`, `web/src/types.ts`, `web/src/app.css` |
| Tests and documentation | Tests directly assert current generated network and two-phase safety behavior; user documentation assumes one default intersection and its existing result files. | `tests/test_simulation.py`, `tests/test_signal_safety.py`, `tests/test_api.py`, `README.md`, `docs/ARCHITECTURE.md`, `docs/DEMO.md`, `docs/LICENSES.md` |

## Planned staged changes

### Stage 1 — site source and provenance

- Add `config/sites/boring_road_patna.yaml` for site identity, center, radius, source date, OSM attribution, road geometry references, and explicit `osm` / `assumed` / `surveyed` provenance on every site property.
- Cache OSM XML under `data/sites/`; the Overpass endpoints tested here did not respond, so the extract was fetched from the OSM API map endpoint instead. Tests must consume the local cache only. Record request metadata and ODbL attribution.
- Save a vector/static confirmation map and a human-readable site facts/unknowns report in `docs/sites/`. Do not infer signalization, lane-use restrictions, or counts from visual appearance alone.
- OSM identifies a fountain node at the Boring Road end, but does not explicitly name the Chauraha or map an island footprint. Keep the candidate site provisional until the snapshot is confirmed; do not model an island shape as measured geometry.
- Current Stage 1 artifacts: `config/sites/boring_road_patna.yaml`, `data/sites/boring_road_patna_2026-10-28.osm`, `docs/sites/boring_road_patna.svg`, `docs/sites/boring_road_patna.md`, and `scripts/sites/render_osm_snapshot.py`. The preview generator reads only the local cache.

### Stage 2 — network build: gate failed

- `scripts/sites/build_osm_site_network.py` builds from the local cache with `netconvert --lefthand --roundabouts.guess --junctions.join --proj.utm`, clipped to the configured 275 m circle.
- Generated outputs: `data/sites/boring_road_patna.net.xml`, `docs/sites/boring_road_patna_network_report.{json,md}`, and `docs/sites/boring_road_patna_network.svg`.
- SUMO 1.28.0 generated 68 interior junctions and a nearest `priority` junction 8.52 m from the candidate fountain point. OSM does not classify the junction as roundabout or signalized; generated `priority` is not a verified real-world control description.
- Connectivity validation checked 152 incoming lanes and failed on lane index 1 at Boring Road edges `603915294#11` and `746885310#4`. OSM says these one-way ways have two lanes but gives no turn-lane assignment; do not add a connection without measured correction. The 50 m focus area has 10 separate SUMO junction nodes and is not silently collapsed to one.
- Geometry comparison checked 688 lane-shape vertices; maximum distance to an OSM road segment was **1.895 m** (p95 **1.616 m**). This is only an alignment diagnostic, not accuracy against a survey.
- Stage 2 remains blocked pending measured lane-use corrections or a revised/confirmed site location. Stage 3 demand, Stage 4 controls, and Stage 5 site runtime/scene integration must not proceed from this incomplete movement graph.

### Stage 2 — reproducible OSM-to-SUMO network

- Add an OSM-specific builder path, keeping `SumoNetworkBuilder` and the generated default network unchanged as the fallback.
- Run `netconvert` with left-hand traffic and roundabout detection; record deterministic options and any script/patch corrections.
- Produce a validation report with junction classification, per-approach lane/source data, movement connectivity, and measured lane-to-OSM geometry deviation. Do not continue to controller work without connected allowed movements and reviewable geometry evidence.

### Stage 3 — site demand and heterogeneous traffic

- Add site-scoped, seeded per-approach assumed demand presets and label uncalibrated runs. Preserve existing default demand behavior.
- Define car, auto-rickshaw, e-rickshaw, two-wheeler, bus, and truck vTypes with each driver/vehicle parameter tagged `assumed`; configure and document sublane lateral resolution.
- Optional observed-count CSV calibration must be explicit and output GEH results; absent counts must never be described as calibrated Patna traffic.

### Stage 4 — control plans and safety

- Derive movement conflicts from generated network links and validate each green group against geometry; preserve yellow and all-red transitions as a final enforced safety layer.
- Add clearly distinguished S0 map-derived as-is behavior and hypothetical S1 fixed / S2 adaptive plans. If OSM identifies a roundabout, choose and label metered entry or hypothetical signal redesign rather than implying signals are present.
- Add property tests and paired same-seed comparisons. Report sample counts, confidence intervals, seed/scenario variability, and wins/losses; never reuse default four-way results as Patna evidence.

### Stage 5 — data-driven rendering and API

- Add a backward-compatible site selector and geometry endpoint. Return local metric coordinates for lane/junction shapes, widths, crossings, and signal positions with provenance metadata.
- Keep the current procedural scene as the default; add an OSM-geometry scene path using left-hand traffic and a camera fitted to site bounds.
- Render OSM building footprints; height from OSM tags or an explicitly approximate, seeded assumption. Treat untagged trees/lamps as cosmetic and label them. Add vector-only mini-map, site selector, attribution, and a `Real vs assumed` panel.
- Do not add third-party imagery, copyrighted map tiles, or decorative features that appear to be measured traffic data.

### Stage 6 — evidence and release gate

- Run a 30 simulated-minute SUMO QA run and report collisions, teleports, and emergency stops from actual simulator counters.
- Re-run geometry alignment/connectivity reports and browser captures at 1440×900 and 1920×1080. Review console/network errors and measure performance without claiming hardware not tested.
- Update README, architecture, licensing/ODbL notes, demo steps, and a final real-vs-assumed limitations report. Keep the default four-way tests and benchmark as a regression control.

## Preservation rules and release gates

1. The no-site/default API request must continue to use the existing four-way network, scene, and safety behavior.
2. Site-specific schema additions are optional/backward-compatible; no existing field is renamed or reinterpreted.
3. The new site cannot be shown as real Patna traffic unless measured counts and calibration evidence are supplied.
4. Do not call a stage passed until its listed artifacts and tests have actually been generated and checked.
5. The Stage 1 candidate is based on OSM features but its identity as the requested Chauraha still needs confirmation. If geometry is inadequate, stop and document that fact instead of synthesizing a false exact layout.
