import math
import numpy as np
from aerosim.interfaces import SensorInterface


class BarometerSensor(SensorInterface):
    """
    High-precision digital barometric altimeter (e.g. MS5611 / BMP280):
    - Standard atmospheric pressure lapse rate
    - Ambient temperature model
    - Pressure altitude with sensor Gaussian noise
    """
    def __init__(self, p0_pa: float = 101325.0, temp0_k: float = 288.15):
        self.p0 = p0_pa
        self.t0 = temp0_k
        self.lapse_rate = 0.0065  # K/m
        self.pressure_pa = p0_pa
        self.temperature_c = 15.0
        self.altitude_m = 0.0

    def update(self, dt: float, state) -> dict:
        true_alt = max(0.0, float(state.position[2]))
        # Barometric formula: P = P0 * (1 - L*h/T0) ^ (g*M / (R*L))
        temp_k = self.t0 - self.lapse_rate * true_alt
        exponent = 5.25588
        base_press = self.p0 * ((temp_k / self.t0) ** exponent)

        # Noise in pressure
        noise_pa = np.random.normal(0, 1.2)
        self.pressure_pa = base_press + noise_pa
        self.temperature_c = temp_k - 273.15

        # Reconstructed altitude from noisy pressure
        self.altitude_m = (self.t0 / self.lapse_rate) * (1.0 - (self.pressure_pa / self.p0) ** (1.0 / exponent))

        return self.get_data()

    def get_data(self) -> dict:
        return {
            "pressure_pa": round(float(self.pressure_pa), 1),
            "temperature_c": round(float(self.temperature_c), 1),
            "baro_altitude_m": round(float(self.altitude_m), 2),
        }
