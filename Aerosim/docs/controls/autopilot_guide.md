# Autopilot Flight Modes & Tuning Guide

AeroSim features a cascading PID flight controller architecture supporting autonomous modes.

## Flight Modes

| Mode | Behavior | Input Mapping |
|---|---|---|
| `DISARMED` | Motors cut off (0 RPM) | Inactive |
| `MANUAL` / `ACRO` | Direct angular rate control | Sticks command rotation rates directly |
| `STABILIZE` | Self-leveling roll and pitch | Sticks command tilt angle $\phi, \theta$ |
| `ALT_HOLD` | Closed-loop barometer altitude lock | Vertical stick commands climb rate ($\pm 3$ m/s) |
| `POS_HOLD` (Loiter) | GPS coordinate lock against wind | Sticks command ground velocity vector |
| `AUTO_TAKEOFF` | Autonomous smooth climb to 8m | Automated sequence |
| `AUTO_LAND` | Controlled descent and ground disarm | Automated sequence |
| `RTH` | Failsafe return to Home GPS point | Automated sequence |
| `MISSION` | Sequential GPS waypoint traversal | Automated sequence |

## PID Tuning Parameters

```json
{
  "altitude_pid": { "kp": 0.35, "ki": 0.12, "kd": 0.25 },
  "position_pid": { "kp": 0.22, "ki": 0.03, "kd": 0.30 },
  "attitude_pid": { "kp": 3.8, "ki": 0.2, "kd": 0.8 },
  "yaw_pid":      { "kp": 2.2, "ki": 0.1, "kd": 0.4 }
}
```

- **Proportional ($K_p$)**: Determines responsiveness to error.
- **Integral ($K_i$)**: Eliminates steady-state offset against wind and battery discharge.
- **Derivative ($K_d$)**: Dampens oscillations and overshoots.
