import numpy as np
from aerosim.autopilot.autopilot import DroneAutopilot, FlightMode
from aerosim.autopilot.pid import PIDController


def test_pid_controller_convergence():
    pid = PIDController(kp=1.0, ki=0.1, kd=0.05, output_min=-1.0, output_max=1.0)
    current = 0.0
    target = 10.0
    for _ in range(50):
        out = pid.update(target, current, 0.02)
        current += out * 0.1
    # Should move significantly towards target
    assert current > 1.0


def test_autopilot_arming_state():
    ap = DroneAutopilot()
    assert not ap.is_armed
    assert ap.mode == FlightMode.DISARMED

    ap.arm()
    assert ap.is_armed
    assert ap.mode == FlightMode.STABILIZE

    ap.disarm()
    assert not ap.is_armed
    assert ap.mode == FlightMode.DISARMED


def test_autopilot_motor_output_when_armed():
    ap = DroneAutopilot()
    ap.arm()
    ap.set_mode(FlightMode.AUTO_TAKEOFF, np.array([0.0, 0.0, 0.15]), 0.0)

    motor_cmds, attitude_cmd = ap.update(
        dt=0.02,
        current_pos=np.array([0.0, 0.0, 0.15]),
        current_vel=np.zeros(3),
        current_rot=np.zeros(3),
        current_ang_vel=np.zeros(3)
    )

    assert len(motor_cmds) == 4
    assert np.all(motor_cmds > 0.3)
