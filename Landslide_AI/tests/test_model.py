import pytest
import pandas as pd
from src.model import LandslidePredictor, WSNLandslidePredictor


def test_regional_predictor_single_inference():
    predictor = LandslidePredictor()
    predictor.load()

    res = predictor.predict_single(
        location="Sikkim",
        rainfall_mm=220.0,
        soil_moisture_percent=88.0,
        slope_degree=45.0,
        elevation_m=1600.0
    )

    assert "probability_percent" in res
    assert 0.0 <= res["probability_percent"] <= 100.0
    assert res["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert "factor_of_safety" in res
    assert "recommendation" in res
    assert res["prediction"] in [0, 1]


def test_regional_predictor_batch_inference():
    predictor = LandslidePredictor()
    predictor.load()

    sample_df = pd.DataFrame([
        {"location": "Sikkim", "rainfall_mm": 200, "soil_moisture_percent": 85, "slope_degree": 42, "elevation_m": 1500},
        {"location": "Assam", "rainfall_mm": 20, "soil_moisture_percent": 30, "slope_degree": 10, "elevation_m": 120},
    ])

    results = predictor.predict_batch(sample_df)
    assert len(results) == 2
    assert "Risk_Level" in results.columns
    assert "Probability_%" in results.columns
    assert "Factor_of_Safety" in results.columns


def test_wsn_predictor_inference():
    predictor = WSNLandslidePredictor()
    predictor.load()

    sample_sensor = {
        "Rainfall_mm": 180.0,
        "Slope_Angle": 55.0,
        "Soil_Saturation": 0.88,
        "Vegetation_Cover": 0.15,
        "Rainfall_3Day": 240.0,
        "Rainfall_7Day": 350.0,
        "Aspect": 240.0,
        "Elevation_m": 1400.0,
        "NDVI_Index": 0.22,
        "Pore_Water_Pressure_kPa": 145.0,
        "Soil_Strain": 0.008,
        "Acoustic_Emission_dB": 75.0,
        "Microseismic_Activity": 0.75,
    }

    res = predictor.predict_sample(sample_sensor)
    assert res["prediction"] in [0, 1]
    assert 0.0 <= res["probability_percent"] <= 100.0
    assert res["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert len(res["top_drivers"]) > 0
