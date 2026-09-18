from panda3d.core import (
    NodePath,
    Vec4,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
)


class DroneModel:

    def __init__(self, parent):

        self.root = parent.attachNewNode("Drone")

        self.body = self._create_box(
            "MainBody",
            (0.55, 0.38, 0.16),
            Vec4(0.06, 0.08, 0.11, 1.0),
        )

        self.body.reparentTo(self.root)

        self.body.setPos(
            0,
            0,
            0
        )

        self.arms = []
        self.motors = []
        self.propellers = []

        arm_positions = [
            (0.48, 0.48),
            (0.48, -0.48),
            (-0.48, -0.48),
            (-0.48, 0.48),
        ]

        for index, (x, y) in enumerate(
            arm_positions,
            start=1
        ):

            arm = self._create_box(
                f"Arm{index}",
                (0.52, 0.055, 0.055),
                Vec4(0.13, 0.16, 0.20, 1.0),
            )

            arm.reparentTo(self.root)

            arm.setPos(
                x * 0.5,
                y * 0.5,
                0
            )

            if x * y > 0:
                arm.setH(45)
            else:
                arm.setH(-45)

            self.arms.append(arm)

            motor = self._create_cylinder(
                f"Motor{index}",
                0.10,
                0.12,
                Vec4(0.035, 0.045, 0.055, 1.0),
            )

            motor.reparentTo(self.root)

            motor.setPos(
                x,
                y,
                0.10
            )

            self.motors.append(motor)

            propeller = self._create_propeller(
                f"Propeller{index}"
            )

            propeller.reparentTo(self.root)

            propeller.setPos(
                x,
                y,
                0.18
            )

            self.propellers.append(
                propeller
            )

        self._create_front_indicator()
        self._create_camera_mount()

    def _create_front_indicator(self):

        front = self._create_box(
            "FrontIndicator",
            (0.18, 0.045, 0.045),
            Vec4(0.95, 0.18, 0.06, 1.0),
        )

        front.reparentTo(self.root)

        front.setPos(
            0.34,
            0,
            0.12
        )

    def _create_camera_mount(self):

        mount = self._create_box(
            "CameraMount",
            (0.12, 0.10, 0.08),
            Vec4(0.025, 0.030, 0.035, 1.0),
        )

        mount.reparentTo(self.root)

        mount.setPos(
            0.30,
            0,
            -0.18
        )

        camera = self._create_box(
            "Camera",
            (0.10, 0.075, 0.075),
            Vec4(0.08, 0.12, 0.16, 1.0),
        )

        camera.reparentTo(
            mount
        )

        camera.setPos(
            0.12,
            0,
            -0.02
        )

    def _create_box(
        self,
        name,
        size,
        color,
    ):

        sx, sy, sz = size

        vertices = [
            (-sx, -sy, -sz),
            (sx, -sy, -sz),
            (sx, sy, -sz),
            (-sx, sy, -sz),
            (-sx, -sy, sz),
            (sx, -sy, sz),
            (sx, sy, sz),
            (-sx, sy, sz),
        ]

        node = GeomNode(name)

        format = GeomVertexFormat.getV3()

        data = GeomVertexData(
            name,
            format,
            Geom.UHStatic
        )

        writer = GeomVertexWriter(
            data,
            "vertex"
        )

        for vertex in vertices:
            writer.addData3(*vertex)

        triangles = GeomTriangles(
            Geom.UHStatic
        )

        faces = [
            (0, 1, 2),
            (0, 2, 3),

            (4, 6, 5),
            (4, 7, 6),

            (0, 4, 5),
            (0, 5, 1),

            (1, 5, 6),
            (1, 6, 2),

            (2, 6, 7),
            (2, 7, 3),

            (3, 7, 4),
            (3, 4, 0),
        ]

        for a, b, c in faces:
            triangles.addVertices(
                a,
                b,
                c
            )

        geometry = Geom(data)

        geometry.addPrimitive(
            triangles
        )

        node.addGeom(
            geometry
        )

        result = NodePath(node)

        result.setColor(
            color
        )

        return result

    def _create_cylinder(
        self,
        name,
        radius,
        height,
        color,
        segments=20,
    ):

        node = GeomNode(name)

        format = (
            GeomVertexFormat.getV3()
        )

        data = GeomVertexData(
            name,
            format,
            Geom.UHStatic
        )

        writer = GeomVertexWriter(
            data,
            "vertex"
        )

        for z in (-height, height):

            for i in range(segments):

                angle = (
                    2.0
                    * 3.141592653589793
                    * i
                    / segments
                )

                x = radius * __import__(
                    "math"
                ).cos(angle)

                y = radius * __import__(
                    "math"
                ).sin(angle)

                writer.addData3(
                    x,
                    y,
                    z
                )

        triangles = GeomTriangles(
            Geom.UHStatic
        )

        for i in range(segments):

            next_i = (
                i + 1
            ) % segments

            bottom_a = i
            bottom_b = next_i

            top_a = (
                segments + i
            )

            top_b = (
                segments + next_i
            )

            triangles.addVertices(
                bottom_a,
                bottom_b,
                top_a
            )

            triangles.addVertices(
                bottom_b,
                top_b,
                top_a
            )

        geometry = Geom(data)

        geometry.addPrimitive(
            triangles
        )

        node.addGeom(
            geometry
        )

        result = NodePath(node)

        result.setColor(
            color
        )

        return result

    def _create_propeller(
        self,
        name,
    ):

        propeller = (
            self._create_box(
                name,
                (0.32, 0.025, 0.012),
                Vec4(
                    0.08,
                    0.35,
                    0.55,
                    1.0
                ),
            )
        )

        return propeller

    def set_transform(
        self,
        position,
        rotation,
    ):

        self.root.setPos(
            float(position[0]),
            float(position[1]),
            float(position[2]),
        )

        self.root.setHpr(
            float(rotation[2]),
            float(rotation[1]),
            float(rotation[0]),
        )

    def update_propellers(
        self,
        rpm,
    ):

        rpm_values = list(rpm)

        for index, propeller in enumerate(
            self.propellers
        ):

            if index >= len(rpm_values):
                break

            rotation = (
                float(rpm_values[index])
                * 0.0008
            )

            propeller.setR(
                propeller.getR()
                + rotation
            )

    def reset(self):

        self.root.setPos(
            0,
            0,
            1
        )

        self.root.setHpr(
            0,
            0,
            0
        )