import numpy as np
from aerosim.interfaces import SensorInterface
from aerosim.navigation.geodesy import ned_to_gps


class GPSSensor(SensorInterface):
    """
    Simulated GNSS Receiver (e.g. u-blox M8N / F9P):
    - Satellites tracking count (14 - 22 sats)
    - HDOP / VDOP (Horizontal/Vertical Dilution of Precision)
    - Fix Type: 3 (3D Fix), 4 (DGPS), 5 (RTK Float), 6 (RTK Fixed)
    - Positional noise
    """
    def __init__(self, origin_lat: float, origin_lon: float, origin_alt: float):
        self.origin_lat = origin_lat
        self.origin_lon = origin_lon
        self.origin_alt = origin_alt

        self.satellites = 18
        self.hdop = 0.8
        self.vdop = 1.1
        self.fix_type = 3  # 3D Fix

        self.lat = origin_lat
        self.lon = origin_lon
        self.alt_msl = origin_alt

    def set_origin(self, lat: float, lon: float, alt: float):
        self.origin_lat = lat
        self.origin_lon = lon
        self.origin_alt = alt

    def update(self, dt: float, state) -> dict:
        # Convert true NED to GPS
        n = float(state.position[0]) + np.random.normal(0, 0.25)
        e = float(state.position[1]) + np.random.normal(0, 0.25)
        d = -float(state.position[2]) + np.random.normal(0, 0.4)

        self.lat, self.lon, self.alt_msl = ned_to_gps(
            n, e, d,
            self.origin_lat, self.origin_lon, self.origin_alt
        )

        return self.get_data()

    def get_data(self) -> dict:
        return {
            "latitude": round(float(self.lat), 7),
            "longitude": round(float(self.lon), 7),
            "altitude_msl": round(float(self.alt_msl), 2),
            "satellites": self.satellites,
            "hdop": self.hdop,
            "fix_type": self.fix_type,
        }
