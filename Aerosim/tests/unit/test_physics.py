import math
import numpy as np
import pytest
from aerosim.physics.quad_physics import QuadPhysics


def test_quad_physics_initial_state():
    physics = QuadPhysics()
    assert physics.altitude >= 0.15
    assert physics.speed == 0.0
    assert physics.battery.percentage == 100.0


def test_quad_physics_thrust_calculation():
    physics = QuadPhysics()
    physics.set_motors([0.8, 0.8, 0.8, 0.8])
    for _ in range(10):
        physics.update_motors(0.02)

    thrusts = physics.get_motor_thrust()
    assert np.all(thrusts > 0.0)
    total_thrust = np.sum(thrusts)
    # Total thrust for 4 motors at 0.8 command should exceed vehicle gravity weight
    assert total_thrust > (physics.mass * physics.gravity)


def test_quad_physics_ground_collision():
    physics = QuadPhysics()
    physics.set_motors([0.0, 0.0, 0.0, 0.0])
    for _ in range(50):
        physics.update(0.02)

    # Drone must not fall below ground level (0.15m)
    assert physics.altitude >= 0.15


def test_quad_physics_battery_discharge():
    physics = QuadPhysics()
    physics.set_motors([1.0, 1.0, 1.0, 1.0])
    for _ in range(100):
        physics.update(0.02)

    assert physics.battery.remaining_mah < physics.battery.capacity_mah
    assert physics.battery.percentage < 100.0
