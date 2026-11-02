"""
Configuration module for Landslide_AI.
Centralizes paths, constants, geographical coordinates, and risk thresholds.
"""

from pathlib import Path
from typing import Dict, List, Any

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
MODELS_DIR = BASE_DIR / "models"

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, SAMPLE_DATA_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Data paths
SAMPLE_DATA_PATH = SAMPLE_DATA_DIR / "landslide_data.csv"
RAW_WSN_DATA_PATH = RAW_DATA_DIR / "wsn_landslide_data.csv"
EXPANDED_REGIONAL_DATA_PATH = PROCESSED_DATA_DIR / "regional_expanded_data.csv"
WSN_TRAIN_DATA_PATH = PROCESSED_DATA_DIR / "wsn_train.csv"
WSN_TEST_DATA_PATH = PROCESSED_DATA_DIR / "wsn_test.csv"

# Model paths
REGIONAL_MODEL_PATH = MODELS_DIR / "landslide_model.pkl"
WSN_MODEL_PATH = MODELS_DIR / "wsn_landslide_model.pkl"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"

# Supported Regional Locations (North Eastern Region & Himalayan Hotspots)
LOCATIONS: List[str] = [
    "Sikkim",
    "Arunachal Pradesh",
    "Assam",
    "Meghalaya",
    "Nagaland",
    "Mizoram",
    "Tripura",
    "Manipur",
    "Himachal Pradesh",
    "Uttarakhand",
]

# Geographic Coordinates & Typical Baseline Elevation for Monitoring Stations
LOCATION_COORDINATES: Dict[str, Dict[str, Any]] = {
    "Sikkim": {"lat": 27.5330, "lon": 88.5122, "elevation": 1650, "district": "Gangtok & Mangan"},
    "Arunachal Pradesh": {"lat": 28.2180, "lon": 94.7278, "elevation": 1800, "district": "Tawang & West Kameng"},
    "Assam": {"lat": 26.2006, "lon": 92.9376, "elevation": 220, "district": "Dima Hasao & Karbi Anglong"},
    "Meghalaya": {"lat": 25.5788, "lon": 91.8933, "elevation": 1490, "district": "East Khasi Hills (Shillong/Cherrapunji)"},
    "Nagaland": {"lat": 25.6751, "lon": 94.1086, "elevation": 1440, "district": "Kohima & Phek"},
    "Mizoram": {"lat": 23.7271, "lon": 92.7176, "elevation": 1130, "district": "Aizawl & Lunglei"},
    "Tripura": {"lat": 23.8315, "lon": 91.2868, "elevation": 280, "district": "Jampui Hills"},
    "Manipur": {"lat": 24.8170, "lon": 93.9368, "elevation": 780, "district": "Noney & Tamenglong"},
    "Himachal Pradesh": {"lat": 31.1048, "lon": 77.1734, "elevation": 2200, "district": "Shimla & Kinnaur"},
    "Uttarakhand": {"lat": 30.3165, "lon": 78.0322, "elevation": 1950, "district": "Chamoli & Joshimath"},
}

# Regional Feature Columns (5 Core Factors)
REGIONAL_FEATURE_COLUMNS: List[str] = [
    "rainfall_mm",
    "soil_moisture_percent",
    "slope_degree",
    "elevation_m",
    "location_Arunachal Pradesh",
    "location_Assam",
    "location_Himachal Pradesh",
    "location_Manipur",
    "location_Meghalaya",
    "location_Mizoram",
    "location_Nagaland",
    "location_Sikkim",
    "location_Tripura",
    "location_Uttarakhand",
]

# Risk Classification Thresholds
RISK_LEVELS: Dict[str, Dict[str, Any]] = {
    "LOW": {
        "min_score": 0.0,
        "max_score": 25.0,
        "label": "Low Risk (Green)",
        "color": "#00e676",
        "action": "Routine observation. Slopes appear stable under current meteorological conditions.",
        "icon": "🟢",
        "alert_stage": "STAGE 0: NORMAL",
    },
    "MODERATE": {
        "min_score": 25.0,
        "max_score": 50.0,
        "label": "Moderate Advisory (Yellow)",
        "color": "#ffeb3b",
        "action": "Heightened vigilance advised. Saturated topsoil on vulnerable cuts and road corridors.",
        "icon": "🟡",
        "alert_stage": "STAGE 1: ADVISORY",
    },
    "HIGH": {
        "min_score": 50.0,
        "max_score": 75.0,
        "label": "High Warning (Orange)",
        "color": "#ff9800",
        "action": "Restrict vehicular movement on mountain highways. Prepare rapid response teams.",
        "icon": "🟠",
        "alert_stage": "STAGE 2: WARNING",
    },
    "CRITICAL": {
        "min_score": 75.0,
        "max_score": 100.0,
        "label": "Critical Danger (Red)",
        "color": "#f44336",
        "action": "IMMEDIATE EVACUATION of downslope settlements. Severe debris flow / catastrophic failure imminent.",
        "icon": "🔴",
        "alert_stage": "STAGE 3: EVACUATION ORDER",
    },
}

# Geotechnical Physics Defaults (Infinite Slope Model)
GEOTECH_DEFAULTS = {
    "effective_cohesion_kpa": 12.0,       # c' (kPa)
    "friction_angle_deg": 32.0,           # phi' (degrees)
    "unit_weight_soil": 19.0,             # gamma (kN/m^3)
    "unit_weight_water": 9.81,            # gamma_w (kN/m^3)
    "soil_depth_m": 2.5,                  # z (m)
}


class Config:
    """Namespace for accessing Landslide AI configuration."""
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    RAW_DATA_DIR = RAW_DATA_DIR
    PROCESSED_DATA_DIR = PROCESSED_DATA_DIR
    SAMPLE_DATA_DIR = SAMPLE_DATA_DIR
    MODELS_DIR = MODELS_DIR

    SAMPLE_DATA_PATH = SAMPLE_DATA_PATH
    RAW_WSN_DATA_PATH = RAW_WSN_DATA_PATH
    EXPANDED_REGIONAL_DATA_PATH = EXPANDED_REGIONAL_DATA_PATH
    WSN_TRAIN_DATA_PATH = WSN_TRAIN_DATA_PATH
    WSN_TEST_DATA_PATH = WSN_TEST_DATA_PATH

    REGIONAL_MODEL_PATH = REGIONAL_MODEL_PATH
    WSN_MODEL_PATH = WSN_MODEL_PATH
    MODEL_METADATA_PATH = MODEL_METADATA_PATH

    LOCATIONS = LOCATIONS
    LOCATION_COORDINATES = LOCATION_COORDINATES
    REGIONAL_FEATURE_COLUMNS = REGIONAL_FEATURE_COLUMNS
    RISK_LEVELS = RISK_LEVELS
    GEOTECH_DEFAULTS = GEOTECH_DEFAULTS
