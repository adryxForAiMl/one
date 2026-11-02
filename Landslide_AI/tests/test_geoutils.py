import pytest
import folium
from src.geoutils import create_landslide_map


def test_create_landslide_map_default():
    fmap = create_landslide_map()
    assert isinstance(fmap, folium.Map)
    html_repr = fmap._repr_html_()
    assert len(html_repr) > 0


def test_create_landslide_map_custom_stations():
    custom_stations = [
        {
            "location": "Sikkim Ridge",
            "lat": 27.33,
            "lon": 88.61,
            "elevation_m": 1650,
            "district": "East Sikkim",
            "risk_level": "CRITICAL",
            "probability_percent": 88.5,
            "rainfall_mm": 195.0,
            "soil_moisture_percent": 85.0,
            "slope_degree": 44.0,
        }
    ]
    fmap = create_landslide_map(stations=custom_stations)
    assert isinstance(fmap, folium.Map)
    html_repr = fmap._repr_html_()
    assert "Sikkim Ridge" in html_repr
