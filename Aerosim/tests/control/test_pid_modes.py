from aerosim.autopilot.pid import PIDController


def test_pid_derivative_filtering():
    pid = PIDController(kp=2.0, ki=0.5, kd=0.2, derivative_filter=0.8)
    out1 = pid.update(1.0, 0.0, 0.02)
    out2 = pid.update(1.0, 0.5, 0.02)
    assert out1 != out2
    assert -1.0 <= out1 <= 1.0
    assert -1.0 <= out2 <= 1.0


def test_pid_integral_anti_windup():
    pid = PIDController(kp=1.0, ki=5.0, kd=0.0, output_min=-1.0, output_max=1.0)
    # Feed large error repeatedly
    for _ in range(100):
        out = pid.update(100.0, 0.0, 0.02)
    assert out <= 1.0
    assert pid.integral <= 1.0
