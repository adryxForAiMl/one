# Dashboard design specification

## Direction

Use a calm white and blue control-room interface. `Project/trafficSignal/config/tokens.py` is the shared palette source for the desktop app. The browser dashboard uses a responsive light layout, locally bundled DM Sans and IBM Plex Mono fonts, live charts, and a procedural Three.js scene.

## Tokens and layout

- Page `#F4F8FF`; cards `#FFFFFF`; subtle surfaces `#EEF4FC`; borders `#E3EAF5`.
- Primary blue `#2563EB`; sky `#38BDF8`; text `#0B1B3A`; muted text `#5B6B88`.
- Green `#16A34A`, amber `#F59E0B`, and red `#DC2626` are reserved for status and signal meaning.
- 8 px spacing rhythm, 14 px card radius, one pixel borders.
- The desktop layout remains a compact control and analytics dashboard. The browser layout combines a control header, intersection scene, live metrics, trends, and decision log. Its intersection/buildings are procedural illustration geometry; live vehicle positions and signals come from SUMO.

## Motion and interaction

Keep simulation updates tied to actual SUMO telemetry. Do not animate or synthesize values. Existing controls remain the authoritative start, pause, stop, and export actions. Any unavailable simulation should be represented as unavailable rather than by placeholder live readings.

## Scope note

Space/R shortcuts and control tooltips are implemented in the desktop dashboard. The browser implementation passes a production TypeScript/Vite build and has live SUMO screenshots reviewed at 1440×900 and 1920×1080. Accessibility and frame-rate review have not been completed. `customtkinter.CTk()` aborts in this managed execution session, so desktop screenshot review was not possible either.
