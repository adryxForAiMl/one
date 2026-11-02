import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from aerosim.hardware.mavlink_bridge import list_serial_ports
from aerosim.navigation.geodesy import PRESET_LOCATIONS
from aerosim.simulation.unified_flight_engine import UnifiedFlightEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AeroSim.Server")

app = FastAPI(title="AeroSim GCS & 3D Flight Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = UnifiedFlightEngine()
connected_websockets: Set[WebSocket] = set()

WEB_DIR = Path(__file__).parent / "web"


@app.on_event("startup")
async def startup_event():
    logger.info("Starting AeroSim 50Hz Flight Engine simulation task...")
    asyncio.create_task(flight_loop())


async def flight_loop():
    """50 Hz simulation and telemetry update loop."""
    dt = 0.02
    last_time = asyncio.get_event_loop().time()

    while True:
        try:
            now = asyncio.get_event_loop().time()
            elapsed = now - last_time
            last_time = now

            # Step flight physics and autopilot
            engine.update(elapsed)

            # Broadcast telemetry to connected web clients
            if connected_websockets:
                telemetry = engine.get_telemetry_snapshot()
                msg = json.dumps({"type": "telemetry", "data": telemetry})

                # Broadcast to all connected sockets
                dead_sockets = set()
                for ws in list(connected_websockets):
                    try:
                        await ws.send_text(msg)
                    except Exception:
                        dead_sockets.add(ws)

                for ws in dead_sockets:
                    connected_websockets.discard(ws)

            # Target 50Hz
            await asyncio.sleep(0.02)
        except Exception as e:
            logger.error(f"Flight loop error: {e}")
            await asyncio.sleep(0.05)


@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "operation_mode": engine.operation_mode,
        "clients_connected": len(connected_websockets),
        "telemetry": engine.get_telemetry_snapshot(),
    }


@app.get("/api/locations")
async def get_locations():
    return {
        "current": engine.current_location.name,
        "presets": {
            k: {
                "name": v.name,
                "city": v.city,
                "country": v.country,
                "latitude": v.latitude,
                "longitude": v.longitude,
                "altitude": v.altitude,
                "description": v.description,
            }
            for k, v in PRESET_LOCATIONS.items()
        }
    }


@app.get("/api/ports")
async def get_ports():
    return {"ports": list_serial_ports()}


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    logger.info(f"New client connected to Telemetry WebSocket. Total clients: {len(connected_websockets)}")

    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                cmd = json.loads(data_text)
                cmd_type = cmd.get("type", "")

                if cmd_type == "sticks":
                    engine.set_pilot_sticks(
                        throttle=cmd.get("throttle", 0.0),
                        pitch=cmd.get("pitch", 0.0),
                        roll=cmd.get("roll", 0.0),
                        yaw=cmd.get("yaw", 0.0)
                    )

                elif cmd_type == "mode":
                    mode_name = cmd.get("mode", "")
                    engine.set_flight_mode(mode_name)

                elif cmd_type == "arm":
                    if cmd.get("arm", False):
                        engine.arm()
                    else:
                        engine.disarm()

                elif cmd_type == "gimbal":
                    engine.set_gimbal(
                        pitch_deg=cmd.get("pitch", -15.0),
                        yaw_deg=cmd.get("yaw", 0.0)
                    )

                elif cmd_type == "wind":
                    engine.set_wind(
                        speed_mps=cmd.get("speed", 0.0),
                        direction_deg=cmd.get("direction", 0.0)
                    )

                elif cmd_type == "location":
                    preset = cmd.get("preset", "")
                    engine.set_location_preset(preset)

                elif cmd_type == "custom_location":
                    engine.set_custom_location(
                        name=cmd.get("name", "Custom Waypoint"),
                        lat=cmd.get("lat", 28.6129),
                        lon=cmd.get("lon", 77.2295),
                        alt=cmd.get("alt", 200.0)
                    )

                elif cmd_type == "mission_upload":
                    wps = cmd.get("waypoints", [])
                    engine.autopilot.mission_mgr.set_waypoints(wps)

                elif cmd_type == "mission_action":
                    act = cmd.get("action", "")
                    if act == "start":
                        engine.autopilot.set_mode(
                            engine.autopilot.mode.__class__.MISSION,
                            engine.physics.state.position,
                            engine.physics.state.rotation[2]
                        )
                    elif act == "pause":
                        engine.autopilot.mission_mgr.pause()
                    elif act == "resume":
                        engine.autopilot.mission_mgr.resume()
                    elif act == "stop":
                        engine.autopilot.mission_mgr.stop()
                    elif act == "clear":
                        engine.autopilot.mission_mgr.clear()

                elif cmd_type == "connect_hardware":
                    port = cmd.get("port", "")
                    baud = cmd.get("baud", 115200)
                    success = engine.connect_hardware(port, baud)
                    await websocket.send_text(json.dumps({
                        "type": "hardware_status",
                        "connected": success,
                        "port": port
                    }))

                elif cmd_type == "disconnect_hardware":
                    engine.disconnect_hardware()
                    await websocket.send_text(json.dumps({
                        "type": "hardware_status",
                        "connected": False
                    }))

                elif cmd_type == "reset":
                    engine.reset_simulation()

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        connected_websockets.discard(websocket)
        logger.info(f"Client disconnected. Remaining clients: {len(connected_websockets)}")
    except Exception as e:
        logger.error(f"WebSocket client handler error: {e}")
        connected_websockets.discard(websocket)


# Mount static assets directory
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run("aerosim.server:app", host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    run_server()
