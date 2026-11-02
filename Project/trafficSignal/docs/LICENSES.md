# Third-party assets and licenses

## Visual assets

No third-party 3D models, textures, HDRIs, or camera imagery are currently used. The default junction, buildings, signals, road markings, trees, and vehicles in the browser scene are procedural geometry created by this project. Do not add remote asset URLs. If third-party art is added later, store the source files under the project and record its author, source URL, license, and required attribution here.

## OpenStreetMap

The provisional Boring Road site cache and vector preview use OpenStreetMap data. © OpenStreetMap contributors. The data is available under the Open Database License (ODbL) 1.0; see [OpenStreetMap's copyright and license page](https://www.openstreetmap.org/copyright). The cached source file is `data/sites/boring_road_patna_2026-10-28.osm`; the extract date and source endpoint are recorded in `config/sites/boring_road_patna.yaml`. Any distribution of OSM-derived databases, including generated networks, must be reviewed for ODbL attribution and share-alike requirements. The site identity and central-island footprint remain unverified. No OSM tiles or imagery are bundled.

## Bundled fonts

The web build imports these font files from the installed Fontsource packages:

| Asset | Package | License | Local license file |
|---|---|---|---|
| DM Sans Variable | `@fontsource-variable/dm-sans` 5.3.0 | SIL Open Font License 1.1 | `web/node_modules/@fontsource-variable/dm-sans/LICENSE` |
| IBM Plex Mono | `@fontsource/ibm-plex-mono` 5.3.0 | SIL Open Font License 1.1 | `web/node_modules/@fontsource/ibm-plex-mono/LICENSE` |

These packages include their font license texts in the local install. Preserve the license and attribution if font files are copied or redistributed outside the package-managed build.

## Runtime and development libraries

The browser code also uses Three.js 0.186.1 (`MIT`), React and React DOM 19.3.1 (`MIT`), and Lucide React 0.468.0 (`ISC`). Their license texts are included with the installed packages under `web/node_modules/`. Verify the exact lockfile version and package license before creating a distribution bundle.
