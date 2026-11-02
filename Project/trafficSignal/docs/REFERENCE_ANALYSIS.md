# Reference image analysis

The supplied images show several traffic products, so this pass uses their shared dark operations-console style and maps their useful panels to the simulator's live SUMO state. Screenshots and illustrative numbers are not embedded as application data.

| Ref | Visual idea | Live dashboard equivalent |
| --- | --- | --- |
| 1 | Dark traffic operations screen with a junction, queue state, charts, and vehicle gauges | Dark control-room theme, live intersection views, queue/wait/speed/travel metrics, and time-series charts |
| 2 | Intersection list and multi-camera surveillance wall | The fixed/adaptive SUMO views show the two real simulation runs. The project has one simulated junction, so the interface does not invent other locations or CCTV feeds. |
| 3 | Aerial digital twin with incident cards and pedestrian/vehicle counts | Live SUMO fleet counts by vehicle type and queue/wait threshold alerts. Pedestrian counts are not part of this simulation. |
| 4 | Isometric intersection explaining connected signals and vehicle-to-infrastructure communication | Live phase sequence, current signal state, green countdown, and the adaptive controller's timing decision. No V2X hardware telemetry is claimed. |
| 5 | Adaptive-control hub connected to traffic-flow detection, sensors, and analytics | Actual induction-loop counts and rates, a four-approach detector diagram, measured flow estimation, and queue/delay charts. |
| 6 | Signal controller with settings and a cycle timeline | Run configuration controls, optimizer output, phase-by-phase sequence, and the live green countdown. |
| 7 | Simple intersection monitor with flow, occupancy, queue, and road status | Live queue, speed, completed trips, wait, and rule-based congestion alerts. Detector occupancy is not currently sampled, so no occupancy percentage is shown. |
| 8 | Aerial city map with sensor coverage around an intersection | A schematic four-approach sensor topology with real per-approach loop counts, flow rates, and queue values. Node positions are illustrative, not geographic coordinates. |
| 9 | Dense dark control-room dashboard with analytics, IoT map, performance score, and anomalies | Dark control-room layout, live detector network, fleet mix, queue/delay charts, decision log, signal plan, and explicit queue/wait alert rules. A synthetic overall score is omitted. |
| 10 | Camera scene with highlighted movement paths and AI safety monitoring | Live SUMO vehicles and signal phases plus the adaptive decision log. Predicted paths, camera detections, and AI anomaly scores are not fabricated. |

The visual analogues use telemetry from the current simulation. The detector diagram is topological, and the alert panel uses visible rule thresholds: 10 queued vehicles on an approach or a 30-second mean wait.
