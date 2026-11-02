# Visual scorecard — critique round 1

Date: 2026-10-26  
Artifact reviewed: `docs/visual/v1-pbr/camera-review/dashboard-1440x900.png`  
Method: manual review of the saved Brave screenshot. Scores are reviewer judgments, not automated image metrics.

| Criterion | Score / 5 | Evidence and finding |
|---|---:|---|
| Dashboard clarity | 4 | Light neutral cards and green/amber/red state colors are readable. The control, telemetry, and comparison hierarchy is clear at 1440×900. |
| Scene composition | 4 | The clean top-of-page capture shows the complete junction in both comparison views, with useful approach context and live traffic. |
| Road and lighting materials | 3 | Asphalt has more surface variation and the neutral environment is coherent. Curbs, intersections, and contact remain visibly procedural. |
| Vehicle form and scale | 3 | Vehicles are visible at useful scale and have varied body colors/forms; the silhouettes still need wheels and stronger class-specific detail. |
| Live-data legibility | 4 | Controller labels, active counts, approach queues, and phase diagnostics remain legible around the scene. |
| Overall visual finish | 3 | The dashboard and scene read clearly, while the 3D scene still needs stronger vehicle detail, more convincing junction geometry, and more varied surroundings. |

## Findings and next actions

1. Capture a separate scene-only hero frame and a clean 1920×1080 comparison with the same controlled SUMO state.
2. Improve vehicle silhouettes and road/junction geometry before adding decorative city detail.
3. Add a repeatable screenshot comparison with an explicit pixel-diff tolerance and contact sheet. No pixel-diff score is claimed in this round.

Round 1 is a manual critique only. The capture workflow now resets scroll before screenshots. No pixel-diff score is claimed.
