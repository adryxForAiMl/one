"""
AeroSim - Professional Drone Flight Simulator & Ground Control Station (GCS)
Supports:
1. 3D Photorealistic Simulation & Real-World Satellite GPS Navigation (Web GCS)
2. Real-World Physical Drone MAVLink Telemetry Bridge (Serial / UDP)
3. Panda3D Legacy Desktop View (--desktop)
"""

import argparse
import sys
import threading
import time
import webbrowser


def run_web_simulator(host: str = "127.0.0.1", port: int = 8000, no_browser: bool = False):
    from aerosim.server import run_server

    url = f"http://{host}:{port}"
    print("\n" + "=" * 70)
    print("   🛸 AEROSIM - PROFESSIONAL DRONE FLIGHT SIMULATOR & GCS 🛸")
    print("=" * 70)
    print(f"[*] Ground Control Station URL : {url}")
    print("[*] 3D Photorealistic Visualizer: ACTIVE (Three.js WebGL)")
    print("[*] Real-World GPS Navigation  : ACTIVE (Leaflet Satellite WGS-84)")
    print("[*] MAVLink Hardware Bridge    : READY (Serial / UDP port 14550)")
    print("[*] Telemetry Frequency        : 50 Hz Live Stream")
    print("=" * 70)
    print("Keyboard Flight Controls:")
    print("   W / S       : Pitch Forward / Backward")
    print("   A / D       : Roll Left / Right")
    print("   R / F       : Throttle Up / Down (Climb / Descend)")
    print("   Q / E       : Yaw Rotate Left / Right")
    print("   T           : Auto Takeoff")
    print("   L           : Auto Land")
    print("   H           : Return To Home (RTH)")
    print("   Space       : Position Hold / Loiter")
    print("=" * 70 + "\n")

    if not no_browser:
        def open_browser():
            time.sleep(1.2)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=open_browser, daemon=True).start()

    run_server(host=host, port=port)


def run_desktop_panda():
    try:
        from direct.showbase.ShowBase import ShowBase
        from direct.task import Task
        from panda3d.core import (
            AmbientLight,
            DirectionalLight,
            Vec4,
            WindowProperties,
            ClockObject,
            TextNode,
        )
        from direct.gui.DirectGui import DirectFrame, DirectLabel
        from aerosim.simulation.flight_system import FlightSystem
        from aerosim.environment.environment import Environment

        class AeroSimDesktop(ShowBase):
            def __init__(self):
                ShowBase.__init__(self)
                self.disableMouse()
                self._setup_window()
                self._setup_lighting()
                self.environment = Environment(self.render)
                self.flight = FlightSystem(self)
                self._setup_camera()
                self._setup_hud()
                self._setup_controls()
                self.clock = ClockObject.getGlobalClock()
                self.taskMgr.add(self.update_simulation, "AeroSimSimulation")

            def _setup_window(self):
                props = WindowProperties()
                props.setTitle("AeroSim - Desktop Flight Simulator")
                props.setSize(1280, 800)
                self.win.requestProperties(props)
                self.setBackgroundColor(0.025, 0.035, 0.055, 1.0)

            def _setup_lighting(self):
                ambient = AmbientLight("AmbientLight")
                ambient.setColor(Vec4(0.35, 0.40, 0.48, 1.0))
                ambient_np = self.render.attachNewNode(ambient)
                self.render.setLight(ambient_np)

                sun = DirectionalLight("Sun")
                sun.setColor(Vec4(0.90, 0.90, 0.82, 1.0))
                sun_np = self.render.attachNewNode(sun)
                sun_np.setHpr(-35, -55, 0)
                self.render.setLight(sun_np)

            def _setup_camera(self):
                self.camera_distance = 8.0
                self.camera_height = 4.0
                self.camera.setPos(0, -8, 4)
                self.camera.lookAt(0, 0, 1)

            def _setup_hud(self):
                self.hud_background = DirectFrame(
                    frameColor=(0.01, 0.015, 0.025, 0.82),
                    frameSize=(-0.30, 0.30, -0.28, 0.28),
                    pos=(-1.05, 0, 0.72)
                )
                self.title = DirectLabel(
                    text="AEROSIM", text_scale=0.055, text_align=TextNode.ALeft,
                    frameColor=(0, 0, 0, 0), pos=(-0.26, 0, 0.21)
                )
                self.telemetry = DirectLabel(
                    text="", text_scale=0.025, text_align=TextNode.ALeft,
                    frameColor=(0, 0, 0, 0), pos=(-0.26, 0, 0.06)
                )

            def _setup_controls(self):
                self.accept("escape", self.userExit)
                self.accept("x", self.flight.reset)

            def update_simulation(self, task):
                dt = min(self.clock.getDt(), 0.05)
                self.flight.update(dt)
                self._update_camera()
                self._update_hud()
                return Task.cont

            def _update_camera(self):
                pos = self.flight.position
                self.camera.setPos(pos[0], pos[1] - 8, pos[2] + 4)
                self.camera.lookAt(pos[0], pos[1], pos[2])

            def _update_hud(self):
                self.telemetry["text"] = (
                    f"ALTITUDE   {self.flight.altitude:6.2f} m\n"
                    f"SPEED      {self.flight.speed:6.2f} m/s\n"
                    f"ROLL       {self.flight.roll:6.1f} deg\n"
                    f"PITCH      {self.flight.pitch:6.1f} deg\n"
                    f"YAW        {self.flight.yaw:6.1f} deg"
                )

        app = AeroSimDesktop()
        app.run()
    except Exception as e:
        print(f"Error launching Panda3D desktop app: {e}")
        print("Falling back to Web Simulator & GCS...")
        run_web_simulator()


def main():
    parser = argparse.ArgumentParser(description="AeroSim Drone Simulator & Ground Control Station")
    parser.add_argument("--desktop", action="store_true", help="Launch legacy Panda3D desktop window")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP address for GCS server (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port for GCS server (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser on launch")

    args = parser.parse_args()

    if args.desktop:
        run_desktop_panda()
    else:
        run_web_simulator(host=args.host, port=args.port, no_browser=args.no_browser)


if __name__ == "__main__":
    main()