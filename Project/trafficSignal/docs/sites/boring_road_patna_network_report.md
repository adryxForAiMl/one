# Boring Road candidate — SUMO network validation

**OSM attribution:** © OpenStreetMap contributors · ODbL 1.0

The site identity is provisional. No signal program or central-island footprint is inferred from missing OSM tags.

## Build and control evidence

- Raw OSM cache: `data/sites/boring_road_patna_2026-10-28.osm` (downloaded 2026-10-28).
- SUMO network: `data/sites/boring_road_patna.net.xml`.
- Converter: `Eclipse SUMO netconvert 1.28.0`.
- UTM frame: EPSG:32645; center 25.6126047, 85.1188289; radius 275.0 m.
- Options: `--lefthand, --roundabouts.guess, --junctions.join, --junctions.join-dist 10, --proj.utm, --keep-edges.in-geo-boundary <48-vertex 275 m circle>, --connection-files boring_road_patna.con.xml (assumed merge patch for Boring Road lane drops)`.
- OSM control classification: unclassified in OSM; missing tags do not establish real-world control. Roundabout ways: none tagged in radius. Signal nodes in radius: none tagged in radius.
- Nearest generated SUMO junction: `9202200713` (`priority`), 8.52 m from the candidate center. The 50 m focus area contains 10 separate generated junction nodes; these are not silently merged into a fabricated single junction.

## Approach lanes

| SUMO junction | Incoming edge | OSM way/name | SUMO lanes | OSM lane tag | Lane-count provenance |
|---|---|---|---:|---:|---|
| `13718180197` | `-1065482352` | `1065482352` (unnamed) | 1 | not tagged | `assumed` |
| `1535219467` | `-1280783696` | `1280783696` (unnamed) | 1 | not tagged | `assumed` |
| `13718180198` | `1065482352` | `1065482352` (unnamed) | 1 | not tagged | `assumed` |
| `1535219467` | `121070865#4` | `121070865` East Boring Canal Road | 1 | not tagged | `assumed` |
| `6989116503` | `121070865#5` | `121070865` East Boring Canal Road | 1 | not tagged | `assumed` |
| `1535148784` | `121070865#6` | `121070865` East Boring Canal Road | 1 | not tagged | `assumed` |
| `13718180197` | `121070865#7` | `121070865` East Boring Canal Road | 1 | not tagged | `assumed` |
| `13718180199` | `1280783696` | `1280783696` (unnamed) | 1 | not tagged | `assumed` |
| `13718180198` | `140114355#1` | `140114355` West Boring Canal Road | 1 | not tagged | `assumed` |
| `9202200713` | `140114355#2` | `140114355` West Boring Canal Road | 1 | not tagged | `assumed` |
| `1535148754` | `140114355#3` | `140114355` West Boring Canal Road | 1 | not tagged | `assumed` |
| `13720104732` | `140114355#4` | `140114355` West Boring Canal Road | 1 | not tagged | `assumed` |
| `13718180199` | `140114355#5` | `140114355` West Boring Canal Road | 1 | not tagged | `assumed` |
| `1535219467` | `140121931#4` | `140121931` (unnamed) | 1 | not tagged | `assumed` |
| `13720104732` | `1498127570` | `1498127570` (unnamed) | 1 | not tagged | `assumed` |
| `13720104731` | `603915294#10` | `603915294` Boring Road | 2 | 2 | `osm` |
| `1535148754` | `603915294#11` | `603915294` Boring Road | 2 | 2 | `osm` |
| `1535148784` | `746885310#4` | `746885310` Boring Road | 2 | 2 | `osm` |

SUMO lane counts shown where OSM has no `lanes` tag are imported defaults, not measured lane counts.

## Connectivity and geometry alignment

- Connectivity: **PASS** — 152 incoming lanes checked at 68 internal junctions; 0 have no generated movement.
- Lane vertices compared: 688. Maximum deviation: **1.895 m**; p95: 1.616 m.
- Deviation compares SUMO lane polylines to OSM road centerline segments in UTM coordinates. It is not a survey-accuracy claim. See [`boring_road_patna_network.svg`](boring_road_patna_network.svg) for the vector overlay.

## Warnings

- Warning: Not joining junctions 12079485436,12079485440,12079653513,12079653514 (only 1 entry node).
- Warning: Not joining junctions 1535148754,9202200713 (only 1 edge within and no cross-traffic).
- Warning: Not joining junctions 14137447802,9199233299 (only 1 entry node).
- Warning: Not joining junctions 1535148784,6989116503 (only 1 edge within and no cross-traffic).
- Warning: Not joining junctions 1535219559,9199233314 (parallel incoming -1552919495,996228844).
- Warning: Speed of straight connection '746885301#1_0->746885301#2_0' reduced by 14.37 due to turning radius of 32.70 (length=3.72, angle=21.68).
- Warning: 7 total messages of type: Not joining junctions % (%).

No junction signal timings are included in this generated geometry report. OSM records a fountain point, not an island boundary or signal program.
