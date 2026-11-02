# TrafficSignal visual direction

## Product direction

Use stylized realism: a clean, bright daylight digital twin with readable road geometry, soft shadows, crisp signal states, and clear separation between live SUMO telemetry and cosmetic scenery. Keep the dashboard white and blue, matching `config/tokens.py`; reserve green, amber, and red for signal/status meanings. Avoid photoreal textures that imply a real camera feed or surveyed location.

## Palette

| Role | Target |
|---|---|
| Page / cards | White `#FFFFFF` with subtle neutral borders |
| Primary UI accent | Clear medium blue from `config/tokens.py` (`#2563EB`) |
| Secondary live accent | Sky blue (`#38BDF8`) for adaptive measurements and links |
| Text | Deep navy `#0B1B3A`, with muted slate for descriptions |
| Signal states | Green `#16A34A`, amber `#F59E0B`, red `#DC2626` |
| 3D daylight | Pale blue sky/ambient fill, warm-neutral key light, restrained saturation |

## Lighting and materials

- Use one warm-neutral directional key light and a soft blue-tinted hemisphere fill, with physically based material response and sRGB output.
- Procedural environment lighting should be generated locally; do not depend on remote HDRI or texture URLs.
- Asphalt should read as charcoal with restrained roughness variation. Curbs and sidewalks use warm concrete. Markings stay high contrast without blooming.
- Vehicle paint uses varied, moderately saturated colors; glass, rubber, and lamp materials remain visually distinct.
- Keep shadows soft and local. Ambient occlusion and bloom should be subtle and independently quality-gated.

## Scale and cameras

- Road lane target: approximately 3.5 m wide.
- Passenger car target: approximately 4.2 m long; scale each class from its SUMO vType dimensions.
- Signal head target: approximately 5 m above ground.
- Default camera: oblique hero angle with the junction legible, not straight overhead.
- Additional presets: street level, selected-vehicle follow, analytic top-down, and a reduced-motion showcase orbit.

## Current audit note

The Stage 0 and Stage A Playwright captures show the current white dashboard with blue UI accents, neutral concrete, charcoal roads, and green/amber/red signal colors. No reference image folder or external artwork was found. Current screenshots and reports are under `docs/visual/baseline/`, `docs/visual/scissor-candidate/`, and `docs/visual/v1-pbr/`. The city scene remains intentionally procedural and illustrative rather than photoreal or geographically surveyed.
