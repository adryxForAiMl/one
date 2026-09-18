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

from direct.gui.DirectGui import (
    DirectFrame,
    DirectLabel,
)

from aerosim.simulation.flight_system import FlightSystem
from aerosim.environment.environment import Environment


class AeroSim(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        self.disableMouse()

        self._setup_window()
        self._setup_lighting()

        self.environment = Environment(
            self.render
        )

        self.flight = FlightSystem(
            self
        )

        self._setup_camera()
        self._setup_hud()
        self._setup_controls()

        self.clock = ClockObject.getGlobalClock()

        self.taskMgr.add(
            self.update_simulation,
            "AeroSimSimulation"
        )

    def _setup_window(self):

        props = WindowProperties()

        props.setTitle(
            "AeroSim - Professional Drone Flight Simulator"
        )

        props.setSize(
            1440,
            900
        )

        self.win.requestProperties(
            props
        )

        self.setBackgroundColor(
            0.025,
            0.035,
            0.055,
            1.0
        )

    def _setup_lighting(self):

        ambient = AmbientLight(
            "AmbientLight"
        )

        ambient.setColor(
            Vec4(
                0.35,
                0.40,
                0.48,
                1.0
            )
        )

        ambient_np = self.render.attachNewNode(
            ambient
        )

        self.render.setLight(
            ambient_np
        )

        sun = DirectionalLight(
            "Sun"
        )

        sun.setColor(
            Vec4(
                0.90,
                0.90,
                0.82,
                1.0
            )
        )

        sun_np = self.render.attachNewNode(
            sun
        )

        sun_np.setHpr(
            -35,
            -55,
            0
        )

        self.render.setLight(
            sun_np
        )

    def _setup_camera(self):

        self.camera_distance = 8.0
        self.camera_height = 4.0

        self.camera.setPos(
            0,
            -8,
            4
        )

        self.camera.lookAt(
            0,
            0,
            1
        )

    def _setup_hud(self):

        self.hud_background = DirectFrame(
            frameColor=(
                0.01,
                0.015,
                0.025,
                0.82
            ),
            frameSize=(
                -0.30,
                0.30,
                -0.28,
                0.28
            ),
            pos=(
                -1.05,
                0,
                0.72
            )
        )

        self.title = DirectLabel(
            text="AEROSIM",
            text_scale=0.055,
            text_align=TextNode.ALeft,
            frameColor=(
                0,
                0,
                0,
                0
            ),
            pos=(
                -0.26,
                0,
                0.21
            )
        )

        self.subtitle = DirectLabel(
            text="PROFESSIONAL DRONE FLIGHT SIMULATOR",
            text_scale=0.020,
            text_align=TextNode.ALeft,
            frameColor=(
                0,
                0,
                0,
                0
            ),
            pos=(
                -0.26,
                0,
                0.15
            )
        )

        self.telemetry = DirectLabel(
            text="",
            text_scale=0.025,
            text_align=TextNode.ALeft,
            frameColor=(
                0,
                0,
                0,
                0
            ),
            pos=(
                -0.26,
                0,
                0.06
            )
        )

        self.controls = DirectLabel(
            text=(
                "ARROW KEYS  Flight\n"
                "R / F       Throttle\n"
                "Q / E       Yaw\n"
                "X           Reset\n"
                "ESC         Exit"
            ),
            text_scale=0.021,
            text_align=TextNode.ALeft,
            frameColor=(
                0,
                0,
                0,
                0
            ),
            pos=(
                -0.26,
                0,
                -0.11
            )
        )

    def _setup_controls(self):

        self.accept(
            "escape",
            self.userExit
        )

        self.accept(
            "x",
            self.flight.reset
        )

    def update_simulation(
        self,
        task
    ):

        dt = min(
            self.clock.getDt(),
            0.05
        )

        self.flight.update(
            dt
        )

        self._update_camera()
        self._update_hud()

        return Task.cont

    def _update_camera(self):

        position = self.flight.position

        yaw = self.flight.yaw

        import math

        yaw_rad = math.radians(
            yaw
        )

        camera_x = (
            position[0]
            - math.sin(yaw_rad)
            * self.camera_distance
        )

        camera_y = (
            position[1]
            - math.cos(yaw_rad)
            * self.camera_distance
        )

        camera_z = (
            position[2]
            + self.camera_height
        )

        current = self.camera.getPos()

        smooth = 0.08

        new_x = current.x + (
            camera_x
            - current.x
        ) * smooth

        new_y = current.y + (
            camera_y
            - current.y
        ) * smooth

        new_z = current.z + (
            camera_z
            - current.z
        ) * smooth

        self.camera.setPos(
            new_x,
            new_y,
            new_z
        )

        self.camera.lookAt(
            position[0],
            position[1],
            position[2]
        )

    def _update_hud(self):

        motor_rpm = self.flight.motor_rpm

        motor_thrust = self.flight.motor_thrust

        self.telemetry["text"] = (
            f"ALTITUDE   {self.flight.altitude:6.2f} m\n"
            f"SPEED      {self.flight.speed:6.2f} m/s\n"
            f"ROLL       {self.flight.roll:6.1f} deg\n"
            f"PITCH      {self.flight.pitch:6.1f} deg\n"
            f"YAW        {self.flight.yaw:6.1f} deg\n"
            f"THROTTLE   {self.flight.throttle * 100:6.1f} %\n"
            f"MOTOR 1    {motor_rpm[0]:6.0f} RPM\n"
            f"MOTOR 2    {motor_rpm[1]:6.0f} RPM\n"
            f"MOTOR 3    {motor_rpm[2]:6.0f} RPM\n"
            f"MOTOR 4    {motor_rpm[3]:6.0f} RPM\n"
            f"THRUST     {motor_thrust.sum():6.2f} N"
        )

    def run_simulation(self):

        self.run()


if __name__ == "__main__":

    simulator = AeroSim()

    simulator.run()