# AeroSim Architecture & Technical Overview

AeroSim is an end-to-end aerial simulation platform and Ground Control Station (GCS) designed for both digital twin modeling and physical drone operations.

```
       +-------------------------------------------------------------+
       |             Web Ground Control Station (GCS) UI             |
       |  - Three.js 3D Viewport      - Aviation Canvas HUD (60fps) |
       |  - Leaflet Satellite Map     - Virtual Sticks / Gamepad     |
       +-------------------------------------------------------------+
                                      ▲  Bi-directional WebSocket
                                      ▼  (50 Hz JSON Stream)
       +-------------------------------------------------------------+
       |                  FastAPI / asyncio Server                   |
       |  - WebSocket Endpoint (/ws/telemetry)                       |
       |  - REST Endpoints (/api/status, /api/locations, /api/ports) |
       +-------------------------------------------------------------+
                                      ▲
                                      ▼
       +-------------------------------------------------------------+
       |                    Unified Flight Engine                    |
       |                                                             |
       |   [SIMULATION MODE]                  [HARDWARE MODE]        |
       |   ├── QuadPhysics (6-DOF)            └── MAVLinkBridge      |
       |   ├── DroneAutopilot (PID)               ├── Serial Port    |
       |   ├── SensorSuite (IMU, GPS, Baro)       └── UDP Socket     |
       |   └── MissionManager (Waypoints)                            |
       +-------------------------------------------------------------+
                                      ▲
                                      ▼
       +-------------------------------------------------------------+
       |               Real-World Navigation (Geodesy)               |
       |  WGS-84 Ellipsoid (Latitude, Longitude, Altitude MSL <-> NED)
       +-------------------------------------------------------------+
```

## Core Subsystems

1. **`aerosim.simulation`**:
   - Manages state orchestration between physics simulation and real-world MAVLink hardware.
2. **`aerosim.physics`**:
   - 6-DOF rigid body equations of motion, 4 brushless motors with thrust curves, aerodynamic drag, battery discharge model, and ground collision constraints.
3. **`aerosim.autopilot`**:
   - State machine with modes: `DISARMED`, `MANUAL`, `STABILIZE`, `ALT_HOLD`, `POS_HOLD`, `AUTO_TAKEOFF`, `AUTO_LAND`, `RTH`, `MISSION`.
4. **`aerosim.hardware`**:
   - Bi-directional Pymavlink bridge for physical drone connections over serial ports or UDP.
5. **`aerosim.sensors`**:
   - Realistic sensor models: IMU (accelerometer/gyroscope with bias drift), barometric altimeter, and GNSS receiver.
6. **`aerosim.missions`**:
   - Waypoint navigation engine with acceptance spheres and loiter timers.
