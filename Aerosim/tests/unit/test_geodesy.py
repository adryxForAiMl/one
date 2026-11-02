import math
from aerosim.navigation.geodesy import (
    haversine_distance,
    bearing_to,
    ned_to_gps,
    gps_to_ned,
    PRESET_LOCATIONS
)


def test_haversine_distance_known():
    # Distance between New Delhi India Gate and Taj Mahal Agra (~180 km)
    delhi_lat, delhi_lon = 28.6129, 77.2295
    agra_lat, agra_lon = 27.1751, 78.0421
    dist = haversine_distance(delhi_lat, delhi_lon, agra_lat, agra_lon)
    assert 170000 < dist < 195000  # ~180 km


def test_ned_to_gps_roundtrip():
    origin = PRESET_LOCATIONS["new_delhi"]
    north_in, east_in, down_in = 150.0, -80.0, -25.0

    lat, lon, alt = ned_to_gps(
        north_in, east_in, down_in,
        origin.latitude, origin.longitude, origin.altitude
    )

    n_out, e_out, d_out = gps_to_ned(
        lat, lon, alt,
        origin.latitude, origin.longitude, origin.altitude
    )

    assert abs(north_in - n_out) < 0.05
    assert abs(east_in - e_out) < 0.05
    assert abs(down_in - d_out) < 0.05
