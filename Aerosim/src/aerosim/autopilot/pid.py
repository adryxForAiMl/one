class PIDController:
    """
    Robust Discrete PID Controller with anti-windup clamping,
    derivative low-pass filtering, and measurement-based derivative.
    """
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        output_min: float = -1.0,
        output_max: float = 1.0,
        integrator_min: float | None = None,
        integrator_max: float | None = None,
        derivative_filter: float = 0.85,
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.integrator_min = integrator_min if integrator_min is not None else output_min
        self.integrator_max = integrator_max if integrator_max is not None else output_max
        self.derivative_filter = derivative_filter

        self.integral = 0.0
        self.last_error = 0.0
        self.last_measurement = 0.0
        self.filtered_derivative = 0.0
        self.initialized = False

    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0
        self.last_measurement = 0.0
        self.filtered_derivative = 0.0
        self.initialized = False

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        if dt <= 0.0:
            return 0.0

        error = setpoint - measurement

        if not self.initialized:
            self.last_measurement = measurement
            self.last_error = error
            self.initialized = True

        # Proportional term
        p_term = self.kp * error

        # Integral term with anti-windup clamping
        self.integral += self.ki * error * dt
        self.integral = max(self.integrator_min, min(self.integrator_max, self.integral))
        i_term = self.integral

        # Derivative on measurement (prevents setpoint kick)
        meas_derivative = (measurement - self.last_measurement) / dt
        # Low pass filter on derivative
        self.filtered_derivative = (
            self.derivative_filter * self.filtered_derivative
            + (1.0 - self.derivative_filter) * meas_derivative
        )
        d_term = -self.kd * self.filtered_derivative

        self.last_measurement = measurement
        self.last_error = error

        output = p_term + i_term + d_term
        return max(self.output_min, min(self.output_max, output))
