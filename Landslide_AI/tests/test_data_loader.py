import pytest
import pandas as pd
from src.data_loader import (
    calculate_factor_of_safety,
    validate_regional_input,
    load_regional_data,
    load_wsn_data,
)
from src.config import LOCATIONS


def test_factor_of_safety_gentle_dry():
    # Gentle slope (12 deg), dry soil (20%) -> should be safe (FS > 1.5)
    fs = calculate_factor_of_safety(slope_deg=12.0, soil_moisture_pct=20.0)
    assert fs > 1.5


def test_factor_of_safety_steep_saturated():
    # Steep slope (50 deg), saturated soil (95%) -> should fail (FS < 1.0)
    fs = calculate_factor_of_safety(slope_deg=50.0, soil_moisture_pct=95.0)
    assert fs < 1.0


def test_validate_regional_input_valid():
    res = validate_regional_input("Sikkim", 100.0, 50.0, 25.0, 1500.0)
    assert res["is_valid"] is True
    assert len(res["errors"]) == 0


def test_validate_regional_input_invalid():
    res = validate_regional_input("InvalidState", -10.0, 150.0, 95.0, -100.0)
    assert res["is_valid"] is False
    assert len(res["errors"]) >= 4


def test_load_regional_data():
    df = load_regional_data()
    assert isinstance(df, pd.DataFrame)
    required_cols = ["location", "rainfall_mm", "soil_moisture_percent", "slope_degree", "elevation_m", "previous_landslide"]
    for col in required_cols:
        assert col in df.columns
    assert len(df) > 0


def test_load_wsn_data():
    df = load_wsn_data()
    assert isinstance(df, pd.DataFrame)
    assert "Label" in df.columns
    assert len(df) > 9000
    assert df.isnull().sum().sum() == 0
