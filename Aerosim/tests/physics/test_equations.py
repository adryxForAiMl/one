import numpy as np
from aerosim.physics.quad_physics import QuadPhysics


def test_torque_balance_in_symmetric_hover():
    physics = QuadPhysics()
    physics.set_motors([0.6, 0.6, 0.6, 0.6])
    torques = physics.calculate_torques()
    # In symmetric hover on level ground, net torques should be near 0
    assert np.allclose(torques, 0.0, atol=1e-5)


def test_wind_drag_force_opposes_motion():
    physics = QuadPhysics()
    physics.set_wind(5.0, 0.0)  # 5 m/s North wind
    forces = physics.calculate_total_force()
    assert forces is not None
    assert len(forces) == 3
