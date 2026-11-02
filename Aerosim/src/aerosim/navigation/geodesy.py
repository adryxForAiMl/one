import math
from dataclasses import dataclass
from typing import Dict, Tuple

# WGS-84 ellipsoid constants
WGS84_A = 6378137.0  # semi-major axis (meters)
WGS84_F = 1.0 / 298.257223563  # flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)  # semi-minor axis
WGS84_E2 = 2 * WGS84_F - WGS84_F**2  # first eccentricity squared


@dataclass
class GeoLocation:
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    altitude: float  # meters MSL
    description: str


PRESET_LOCATIONS: Dict[str, GeoLocation] = {
    "new_york": GeoLocation(
        name="Manhattan & Central Park Skyline",
        city="New York City",
        country="USA",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        description="Iconic Manhattan skyline, Hudson River waterfront, and Central Park airspace."
    ),
    "new_delhi": GeoLocation(
        name="India Gate & Kartavya Path",
        city="New Delhi",
        country="India",
        latitude=28.6129,
        longitude=77.2295,
        altitude=215.0,
        description="Historical boulevard and drone corridor in central New Delhi."
    ),
    "mumbai": GeoLocation(
        name="Marine Drive & Gateway",
        city="Mumbai",
        country="India",
        latitude=18.9220,
        longitude=72.8347,
        altitude=14.0,
        description="Arabian sea coastal flight zone and harbor promenade."
    ),
    "bengaluru": GeoLocation(
        name="Electronic City Drone Hub",
        city="Bengaluru",
        country="India",
        latitude=12.8452,
        longitude=77.6602,
        altitude=900.0,
        description="High-altitude technology campus corridor in South India."
    ),
    "san_francisco": GeoLocation(
        name="Golden Gate Strait & Crissy Field",
        city="San Francisco",
        country="USA",
        latitude=37.8024,
        longitude=-122.4646,
        altitude=15.0,
        description="Scenic coastal bay flight with ocean winds and bridge views."
    ),
    "dubai": GeoLocation(
        name="Dubai Marina & Skyway",
        city="Dubai",
        country="UAE",
        latitude=25.0772,
        longitude=55.1330,
        altitude=8.0,
        description="Futuristic coastal towers and calm Arabian Gulf airspace."
    ),
    "swiss_alps": GeoLocation(
        name="Interlaken Alpine Valley",
        city="Interlaken",
        country="Switzerland",
        latitude=46.6863,
        longitude=7.8632,
        altitude=566.0,
        description="Alpine lake valley surrounded by 4000m glacial peaks."
    ),
    "tokyo": GeoLocation(
        name="Tokyo Bay Airspace",
        city="Tokyo",
        country="Japan",
        latitude=35.6264,
        longitude=139.7744,
        altitude=6.0,
        description="Modern bay zone overlooking Rainbow Bridge and Odaiba."
    )
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two GPS coordinates in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def bearing_to(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate initial bearing from point 1 to point 2 in degrees (0-360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    theta = math.atan2(y, x)
    return (math.degrees(theta) + 360.0) % 360.0


def ned_to_gps(
    north: float,
    east: float,
    down: float,
    origin_lat: float,
    origin_lon: float,
    origin_alt: float
) -> Tuple[float, float, float]:
    """
    Convert local Cartesian NED coordinates (in meters) to global GPS (Lat, Lon, Alt).
    North (X), East (Y), Down (-Z) relative to home origin.
    """
    lat_rad = math.radians(origin_lat)
    
    # Radii of curvature
    sin_lat = math.sin(lat_rad)
    r_n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)  # prime vertical
    r_m = WGS84_A * (1.0 - WGS84_E2) / ((1.0 - WGS84_E2 * sin_lat * sin_lat) ** 1.5)  # meridian

    d_lat = north / (r_m + origin_alt)
    d_lon = east / ((r_n + origin_alt) * math.cos(lat_rad))

    lat = origin_lat + math.degrees(d_lat)
    lon = origin_lon + math.degrees(d_lon)
    alt = origin_alt - down

    return lat, lon, alt


def gps_to_ned(
    lat: float,
    lon: float,
    alt: float,
    origin_lat: float,
    origin_lon: float,
    origin_alt: float
) -> Tuple[float, float, float]:
    """
    Convert global GPS (Lat, Lon, Alt) to local Cartesian NED (North, East, Down in meters).
    """
    lat_rad = math.radians(origin_lat)
    sin_lat = math.sin(lat_rad)

    r_n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    r_m = WGS84_A * (1.0 - WGS84_E2) / ((1.0 - WGS84_E2 * sin_lat * sin_lat) ** 1.5)

    d_lat_rad = math.radians(lat - origin_lat)
    d_lon_rad = math.radians(lon - origin_lon)

    north = d_lat_rad * (r_m + origin_alt)
    east = d_lon_rad * (r_n + origin_alt) * math.cos(lat_rad)
    down = -(alt - origin_alt)

    return north, east, down
