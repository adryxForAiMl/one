"""
Data Loader and Preprocessing Pipeline for Landslide_AI.
Handles data ingestion, validation, physical slope stability simulation,
and dataset partitioning.
"""

import math
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional

from src.config import (
    SAMPLE_DATA_PATH,
    RAW_WSN_DATA_PATH,
    EXPANDED_REGIONAL_DATA_PATH,
    WSN_TRAIN_DATA_PATH,
    WSN_TEST_DATA_PATH,
    LOCATIONS,
    LOCATION_COORDINATES,
    GEOTECH_DEFAULTS,
)


def calculate_factor_of_safety(
    slope_deg: float,
    soil_moisture_pct: float,
    c_prime: float = GEOTECH_DEFAULTS["effective_cohesion_kpa"],
    phi_deg: float = GEOTECH_DEFAULTS["friction_angle_deg"],
    gamma: float = GEOTECH_DEFAULTS["unit_weight_soil"],
    gamma_w: float = GEOTECH_DEFAULTS["unit_weight_water"],
    z: float = GEOTECH_DEFAULTS["soil_depth_m"],
) -> float:
    """
    Calculate geotechnical Factor of Safety (FS) using the Infinite Slope Stability Model.
    FS < 1.0 indicates unstable slope failure (landslide).
    FS >= 1.0 indicates stable slope.
    """
    beta = math.radians(max(0.5, slope_deg))
    phi = math.radians(phi_deg)
    
    # Saturation ratio m (0.0 to 1.0)
    m = min(1.0, max(0.0, soil_moisture_pct / 100.0))
    
    sin_beta = math.sin(beta)
    cos_beta = math.cos(beta)
    
    # Resisting shear strength (Coulomb-Terzaghi)
    normal_stress = (gamma - m * gamma_w) * z * (cos_beta ** 2)
    shear_strength = c_prime + normal_stress * math.tan(phi)
    
    # Mobilized shear stress
    shear_stress = gamma * z * sin_beta * cos_beta
    
    if shear_stress <= 0:
        return 5.0
        
    fs = shear_strength / shear_stress
    return float(max(0.1, min(10.0, fs)))


def generate_expanded_regional_dataset(
    n_samples: int = 2500,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generate an expanded, physically-calibrated regional dataset
    grounded in geotechnical mechanics and monsoon hydrology for NER and Himalayan states.
    """
    np.random.seed(random_state)
    records = []

    for _ in range(n_samples):
        loc = np.random.choice(LOCATIONS)
        base_elev = LOCATION_COORDINATES[loc]["elevation"]
        
        # Elevation variation around regional base
        elev = max(100.0, float(np.random.normal(base_elev, base_elev * 0.25)))
        
        # Slope angle distribution (Himalayas & NER have steep terrain, 5 to 65 deg)
        slope = float(np.random.beta(2.5, 3.0) * 65.0 + 3.0)
        
        # Monsoon rainfall distribution (log-normal, 0 to 350 mm/day)
        rainfall = float(np.random.exponential(scale=70.0) + np.random.uniform(0, 40))
        rainfall = min(350.0, rainfall)
        
        # Soil moisture is influenced by recent rainfall and elevation
        moisture_base = 25.0 + (rainfall / 350.0) * 60.0 + np.random.normal(0, 8.0)
        moisture = float(np.clip(moisture_base, 10.0, 98.0))
        
        # Compute Infinite Slope Factor of Safety
        fs = calculate_factor_of_safety(slope, moisture)
        
        # Hydrological trigger condition (empirical rainfall threshold)
        # Intense rainfall (>120mm) + steep slope (>25 deg) triggers failure
        rainfall_hazard = (rainfall > 120.0 and slope > 22.0 and moisture > 65.0)
        critical_fs_failure = (fs < 1.0)
        
        # Probabilistic landslide occurrence
        if critical_fs_failure or rainfall_hazard:
            landslide = 1 if np.random.rand() < 0.92 else 0
        elif fs < 1.25 and rainfall > 80.0:
            landslide = 1 if np.random.rand() < 0.65 else 0
        elif fs < 1.5 and moisture > 75.0:
            landslide = 1 if np.random.rand() < 0.35 else 0
        else:
            landslide = 1 if np.random.rand() < 0.04 else 0
            
        records.append({
            "location": loc,
            "rainfall_mm": round(rainfall, 2),
            "soil_moisture_percent": round(moisture, 2),
            "slope_degree": round(slope, 2),
            "elevation_m": round(elev, 2),
            "previous_landslide": int(landslide)
        })

    # Also ensure original 20 seed samples are preserved
    if SAMPLE_DATA_PATH.exists():
        try:
            original_sample = pd.read_csv(SAMPLE_DATA_PATH)
            for _, row in original_sample.iterrows():
                records.append({
                    "location": row["location"],
                    "rainfall_mm": float(row["rainfall_mm"]),
                    "soil_moisture_percent": float(row["soil_moisture_percent"]),
                    "slope_degree": float(row["slope_degree"]),
                    "elevation_m": float(row["elevation_m"]),
                    "previous_landslide": int(row["previous_landslide"])
                })
        except Exception:
            pass

    df = pd.DataFrame(records)
    # Save to processed directory
    df.to_csv(EXPANDED_REGIONAL_DATA_PATH, index=False)
    return df


def load_regional_data(use_expanded: bool = True) -> pd.DataFrame:
    """
    Load regional dataset. If use_expanded is True and expanded dataset doesn't exist,
    it automatically generates it.
    """
    if use_expanded:
        if not EXPANDED_REGIONAL_DATA_PATH.exists():
            return generate_expanded_regional_dataset()
        return pd.read_csv(EXPANDED_REGIONAL_DATA_PATH)
    
    if SAMPLE_DATA_PATH.exists():
        return pd.read_csv(SAMPLE_DATA_PATH)
    
    # Fallback to generating
    return generate_expanded_regional_dataset()


def load_wsn_data() -> pd.DataFrame:
    """
    Load raw 9,864-sample WSN geotechnical sensor dataset.
    """
    if not RAW_WSN_DATA_PATH.exists():
        raise FileNotFoundError(f"WSN dataset not found at: {RAW_WSN_DATA_PATH}")
    return pd.read_csv(RAW_WSN_DATA_PATH)


def prepare_wsn_splits(
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits the WSN dataset into stratified training and testing sets,
    and caches them in data/processed/.
    """
    from sklearn.model_selection import train_test_split

    df = load_wsn_data()
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df["Label"]
    )
    
    train_df.to_csv(WSN_TRAIN_DATA_PATH, index=False)
    test_df.to_csv(WSN_TEST_DATA_PATH, index=False)
    return train_df, test_df


def validate_regional_input(
    location: str,
    rainfall_mm: float,
    soil_moisture_percent: float,
    slope_degree: float,
    elevation_m: float
) -> Dict[str, Any]:
    """
    Validates user input values and bounds.
    """
    errors = []
    if location not in LOCATIONS:
        errors.append(f"Location '{location}' is not recognized. Expected one of: {LOCATIONS}")
    if rainfall_mm < 0 or rainfall_mm > 2500:
        errors.append(f"Rainfall ({rainfall_mm} mm) must be between 0 and 2500 mm.")
    if soil_moisture_percent < 0 or soil_moisture_percent > 100:
        errors.append(f"Soil moisture ({soil_moisture_percent}%) must be between 0% and 100%.")
    if slope_degree < 0 or slope_degree > 90:
        errors.append(f"Slope angle ({slope_degree}°) must be between 0° and 90°.")
    if elevation_m < 0 or elevation_m > 9000:
        errors.append(f"Elevation ({elevation_m} m) must be between 0 and 9000 m.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
