from panda3d.core import (
    CardMaker,
    LineSegs,
    Vec4,
)


class Environment:

    def __init__(self, render):
        self.render = render

        self.ground = None
        self.grid = None

        self._create_ground()
        self._create_grid()

    def _create_ground(self):

        ground_maker = CardMaker(
            "FlightGround"
        )

        ground_maker.setFrame(
            -100,
            100,
            -100,
            100
        )

        self.ground = self.render.attachNewNode(
            ground_maker.generate()
        )

        self.ground.setP(-90)

        self.ground.setZ(0)

        self.ground.setColor(
            Vec4(
                0.045,
                0.060,
                0.075,
                1.0
            )
        )

    def _create_grid(self):

        grid = LineSegs(
            "FlightGrid"
        )

        grid.setThickness(
            1.0
        )

        for value in range(
            -100,
            101,
            5
        ):

            grid.moveTo(
                value,
                -100,
                0.01
            )

            grid.drawTo(
                value,
                100,
                0.01
            )

            grid.moveTo(
                -100,
                value,
                0.01
            )

            grid.drawTo(
                100,
                value,
                0.01
            )

        self.grid = self.render.attachNewNode(
            grid.create()
        )

        self.grid.setColor(
            Vec4(
                0.10,
                0.16,
                0.20,
                1.0
            )
        )

    def reset(self):
        pass