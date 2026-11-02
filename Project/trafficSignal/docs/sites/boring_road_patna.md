# Boring Road Chauraha, Patna — OSM evidence and assumptions

**Status:** provisional site match; do not treat as calibrated Patna traffic.  
**Required scenario label:** “Simulation on real road geometry with assumed demand”.  
**OSM attribution:** © OpenStreetMap contributors. Data available under the Open Database License (ODbL) 1.0.

## Source and candidate location

- Extract downloaded 2026-10-28 from the OpenStreetMap API map endpoint and cached at [`../../data/sites/boring_road_patna_2026-10-28.osm`](../../data/sites/boring_road_patna_2026-10-28.osm). Overpass requests timed out or could not resolve from this environment.
- Candidate center is **25.6126047, 85.1188289**, OSM node `13683758749`, tagged `amenity=fountain`.
- The fountain node is within 10 m of the mapped end of Boring Road (OSM way `603915294`, `highway=tertiary`, `lanes=2`, `oneway=yes`). This is evidence for a candidate location, not a proof of the local junction name.
- The requested names “Boring Road Chauraha” and “Boring Road Crossing”, and the official road name “Jai Prakash Narayan Path”, were not returned as OSM names in the inspected extract; they remain task-provided labels.
- The OSM fountain is a point. The extract does not establish a central-island boundary or fountain footprint. The SVG preview shows the OSM vectors and a 275 m radius for human confirmation; no imagery or map tiles are used.

## Real vs assumed

| Property | Evidence/value | Provenance |
|---|---|---|
| Boring Road geometry | OSM way `603915294` | `osm` |
| Boring Road classification | `highway=tertiary` | `osm` |
| Boring Road lane count/direction | `lanes=2`, `oneway=yes` on the mapped way | `osm` |
| Candidate center feature | `amenity=fountain`, node `13683758749` | `osm` |
| Island boundary | Not encoded by this point; unknown | `osm` (absence is not a measured boundary) |
| Junction identity as the requested Chauraha | Not explicitly named in the extract; provisional | `assumed` |
| Signal presence/program and exact junction control | No signal node is mapped within the selected 275 m radius; the nearest tagged node in the wider extract is about 503 m away. This does not establish whether the real junction is signalized. | `osm` |
| Other approach lanes and turn restrictions | Unknown until all relevant map features are validated | `osm` |
| Boring Road lane-specific turns | Two lanes are mapped, but lane-use tags are absent; connectivity currently fails for lane 1 at two approach edges | `osm` |
| Radius | 275 m, selected within the requested range | `assumed` |
| Demand | No observed counts provided; uncalibrated assumed flows | `assumed` |
| Vehicle/driver parameters and missing building heights | Not measured; must remain labeled assumptions if modeled | `assumed` |
| Trees, lamps, or other scene decoration absent from OSM | Cosmetic only; not traffic observations | `assumed` |

The site must remain provisional until the user confirms the preview depicts the intended location. Do not assign a roundabout, priority, or signalized control plan based on this evidence alone. The generated Stage 2 network contains multiple junction nodes near the candidate center. Its connectivity gate currently fails for lane 1 on Boring Road ways `603915294` and `746885310`: the available map tags do not establish whether those lanes may turn into the only generated exit. Do not fabricate lane connections. Stage 2 is blocked until that movement is confirmed from measured data or the site is corrected.
