from typing import Dict, Any
from aerosim.sensors.imu import IMUSensor
from aerosim.sensors.barometer import BarometerSensor
from aerosim.sensors.gps_sensor import GPSSensor


class SensorSuite:
    """Integrated avionics sensor suite for the quadcopter."""
    def __init__(self, origin_lat: float = 28.6129, origin_lon: float = 77.2295, origin_alt: float = 215.0):
        self.imu = IMUSensor()
        self.barometer = BarometerSensor()
        self.gps = GPSSensor(origin_lat, origin_lon, origin_alt)

    def set_origin(self, lat: float, lon: float, alt: float):
        self.gps.set_origin(lat, lon, alt)

    def update(self, dt: float, state: Any) -> Dict[str, Any]:
        imu_data = self.imu.update(dt, state)
        baro_data = self.barometer.update(dt, state)
        gps_data = self.gps.update(dt, state)

        return {
            "imu": imu_data,
            "barometer": baro_data,
            "gps": gps_data,
        }
