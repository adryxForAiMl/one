"""
Machine Learning Model Architectures, Inferences, and Calibrations for Landslide_AI.
Contains LandslidePredictor (Regional 5-factor model) and WSNLandslidePredictor (34-sensor IoT model).
"""

import datetime
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from src.config import (
    REGIONAL_MODEL_PATH,
    WSN_MODEL_PATH,
    REGIONAL_FEATURE_COLUMNS,
    LOCATIONS,
    RISK_LEVELS,
)
from src.data_loader import calculate_factor_of_safety


class LandslidePredictor:
    """
    Production-grade Regional Landslide Risk Predictor.
    Predicts landslide likelihood based on Regional Location, Rainfall, Soil Moisture,
    Slope Angle, and Elevation.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or str(REGIONAL_MODEL_PATH)
        self.model = None
        self.metadata = {}
        self.feature_columns = list(REGIONAL_FEATURE_COLUMNS)

    def load(self, model_path: Optional[str] = None) -> "LandslidePredictor":
        """
        Loads the model from disk, supporting both dictionary bundles and raw model objects.
        """
        path = model_path or self.model_path
        data = joblib.load(path)

        if isinstance(data, dict):
            self.model = data.get("model")
            self.metadata = data
            self.feature_columns = (
                data.get("feature_columns")
                or data.get("features")
                or getattr(self.model, "feature_names_in_", None)
                or REGIONAL_FEATURE_COLUMNS
            )
            self.feature_columns = list(self.feature_columns)
        else:
            self.model = data
            self.metadata = {}
            if hasattr(self.model, "feature_names_in_"):
                self.feature_columns = list(self.model.feature_names_in_)
            else:
                self.feature_columns = list(REGIONAL_FEATURE_COLUMNS)

        return self

    def save(self, model_path: Optional[str] = None):
        """
        Saves model and metadata to disk with rich MLOps serialization.
        """
        path = model_path or self.model_path
        payload = {
            "model": self.model,
            "feature_columns": self.feature_columns,
            "features": self.feature_columns,  # backward compatibility
            "locations": self.metadata.get("locations", LOCATIONS),
            "model_name": self.metadata.get("model_name", "Random Forest (Calibrated Regional)"),
            "metrics": self.metadata.get("metrics", {}),
            "created_at": datetime.datetime.now().isoformat(),
            "version": "2.0.0",
        }
        joblib.dump(payload, path)

    def train(
        self,
        df: pd.DataFrame,
        n_estimators: int = 150,
        max_depth: int = 10,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train the Regional Random Forest Classifier on input DataFrame.
        """
        # One-hot encode location column
        encoded_df = pd.get_dummies(df, columns=["location"], dtype=int)

        X = encoded_df.drop("previous_landslide", axis=1, errors="ignore")
        y = encoded_df["previous_landslide"]

        self.feature_columns = X.columns.tolist()

        base_rf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=random_state,
            class_weight="balanced"
        )
        
        base_rf.fit(X, y)
        self.model = base_rf

        # Evaluate on training split for baseline metrics
        preds = base_rf.predict(X)
        probs = base_rf.predict_proba(X)[:, 1] if hasattr(base_rf, "predict_proba") else preds

        metrics = {
            "Accuracy": round(float(accuracy_score(y, preds)), 4),
            "Precision": round(float(precision_score(y, preds, zero_division=0)), 4),
            "Recall": round(float(recall_score(y, preds, zero_division=0)), 4),
            "F1 Score": round(float(f1_score(y, preds, zero_division=0)), 4),
            "ROC-AUC": round(float(roc_auc_score(y, probs)), 4),
        }

        self.metadata = {
            "metrics": metrics,
            "model_name": "RandomForestClassifier (Regional Ensemble)",
            "locations": LOCATIONS,
            "sample_count": len(df)
        }
        return metrics

    def _prepare_vector(
        self,
        location: str,
        rainfall_mm: float,
        soil_moisture_percent: float,
        slope_degree: float,
        elevation_m: float
    ) -> pd.DataFrame:
        """
        Formats single observation into encoded feature vector matching trained columns.
        """
        raw_df = pd.DataFrame([{
            "location": location,
            "rainfall_mm": float(rainfall_mm),
            "soil_moisture_percent": float(soil_moisture_percent),
            "slope_degree": float(slope_degree),
            "elevation_m": float(elevation_m)
        }])

        encoded = pd.get_dummies(raw_df, columns=["location"], dtype=int)
        aligned = encoded.reindex(columns=self.feature_columns, fill_value=0)
        return aligned

    def predict_single(
        self,
        location: str,
        rainfall_mm: float,
        soil_moisture_percent: float,
        slope_degree: float,
        elevation_m: float
    ) -> Dict[str, Any]:
        """
        Performs full inference returning probability, risk classification,
        Factor of Safety, and civil protection recommendations.
        """
        if self.model is None:
            self.load()

        vector = self._prepare_vector(
            location=location,
            rainfall_mm=rainfall_mm,
            soil_moisture_percent=soil_moisture_percent,
            slope_degree=slope_degree,
            elevation_m=elevation_m
        )

        pred_val = int(self.model.predict(vector)[0])
        
        # Calculate calibrated probability
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(vector)[0]
            classes = list(getattr(self.model, "classes_", [0, 1]))
            if 1 in classes:
                c_idx = classes.index(1)
                prob = float(probs[c_idx] * 100.0)
            else:
                prob = float(probs[-1] * 100.0)
        else:
            prob = 100.0 if pred_val == 1 else 0.0

        prob = min(100.0, max(0.0, prob))

        # Risk level determination
        if prob >= 75.0:
            level = "CRITICAL"
        elif prob >= 50.0:
            level = "HIGH"
        elif prob >= 25.0:
            level = "MODERATE"
        else:
            level = "LOW"

        info = RISK_LEVELS[level]
        fs = calculate_factor_of_safety(slope_degree, soil_moisture_percent)

        # Environmental factor interpretations
        triggers = []
        if rainfall_mm >= 150.0:
            triggers.append(f"Torrential monsoon downpour ({rainfall_mm:.1f} mm/24h)")
        elif rainfall_mm >= 80.0:
            triggers.append(f"Significant rainfall ({rainfall_mm:.1f} mm/24h)")

        if soil_moisture_percent >= 75.0:
            triggers.append(f"Near-saturated subsurface pores ({soil_moisture_percent:.1f}%)")

        if slope_degree >= 35.0:
            triggers.append(f"Critical angle of repose exceeded ({slope_degree:.1f}°)")

        if fs < 1.0:
            triggers.append(f"Geotechnical limit state reached (FS={fs:.2f} < 1.0)")

        return {
            "prediction": pred_val,
            "prediction_label": "Landslide Hazard Present" if pred_val == 1 else "Stable Terrain",
            "probability_percent": round(prob, 1),
            "risk_level": level,
            "color": info["color"],
            "alert_stage": info["alert_stage"],
            "recommendation": info["action"],
            "icon": info["icon"],
            "factor_of_safety": round(fs, 2),
            "is_geotechnically_stable": fs >= 1.0,
            "triggers": triggers,
            "location": location,
            "inputs": {
                "rainfall_mm": rainfall_mm,
                "soil_moisture_percent": soil_moisture_percent,
                "slope_degree": slope_degree,
                "elevation_m": elevation_m,
            }
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Performs batch inference on a pandas DataFrame with location, rainfall_mm,
        soil_moisture_percent, slope_degree, elevation_m columns.
        """
        results = []
        for _, row in df.iterrows():
            res = self.predict_single(
                location=row["location"],
                rainfall_mm=float(row["rainfall_mm"]),
                soil_moisture_percent=float(row["soil_moisture_percent"]),
                slope_degree=float(row["slope_degree"]),
                elevation_m=float(row["elevation_m"])
            )
            results.append({
                "Risk_Level": res["risk_level"],
                "Probability_%": res["probability_percent"],
                "Prediction": res["prediction"],
                "Factor_of_Safety": res["factor_of_safety"],
                "Alert_Stage": res["alert_stage"],
                "Recommendation": res["recommendation"]
            })
            
        res_df = pd.DataFrame(results)
        return pd.concat([df.reset_index(drop=True), res_df], axis=1)


class WSNLandslidePredictor:
    """
    Advanced Deep Geotechnical Sensor Model (34 Parameters).
    Trained on Wireless Sensor Network (WSN) telemetry: pore water pressure,
    vibration acoustic emission, soil strain, multi-day rainfall, etc.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or str(WSN_MODEL_PATH)
        self.model = None
        self.scaler = None
        self.feature_columns = []
        self.metadata = {}

    def load(self, model_path: Optional[str] = None) -> "WSNLandslidePredictor":
        """
        Load WSN sensor model and scaler artifact.
        """
        path = model_path or self.model_path
        payload = joblib.load(path)
        self.model = payload["model"]
        self.scaler = payload.get("scaler")
        self.feature_columns = payload["feature_columns"]
        self.metadata = payload
        return self

    def save(self, model_path: Optional[str] = None):
        """
        Save WSN model bundle.
        """
        path = model_path or self.model_path
        payload = {
            "model": self.model,
            "scaler": self.scaler,
            "feature_columns": self.feature_columns,
            "metadata": self.metadata,
            "model_name": "WSN Geotechnical Sensor Classifier (Random Forest)",
            "created_at": datetime.datetime.now().isoformat(),
            "version": "2.0.0"
        }
        joblib.dump(payload, path)

    def train(
        self,
        df: pd.DataFrame,
        n_estimators: int = 150,
        max_depth: int = 14,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train WSN model on raw 34 sensor features.
        """
        X = df.drop("Label", axis=1, errors="ignore")
        y = df["Label"]

        self.feature_columns = X.columns.tolist()

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        rf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        rf.fit(X_scaled, y)
        self.model = rf

        preds = rf.predict(X_scaled)
        probs = rf.predict_proba(X_scaled)[:, 1]

        metrics = {
            "Accuracy": round(float(accuracy_score(y, preds)), 4),
            "Precision": round(float(precision_score(y, preds, zero_division=0)), 4),
            "Recall": round(float(recall_score(y, preds, zero_division=0)), 4),
            "F1 Score": round(float(f1_score(y, preds, zero_division=0)), 4),
            "ROC-AUC": round(float(roc_auc_score(y, probs)), 4),
        }
        self.metadata["metrics"] = metrics
        return metrics

    def predict_sample(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict single WSN IoT sensor reading.
        """
        if self.model is None:
            self.load()

        df_row = pd.DataFrame([feature_dict])
        aligned = df_row.reindex(columns=self.feature_columns, fill_value=0.0)

        if self.scaler is not None:
            X_scaled = self.scaler.transform(aligned)
        else:
            X_scaled = aligned.values

        pred = int(self.model.predict(X_scaled)[0])
        prob = float(self.model.predict_proba(X_scaled)[0][1] * 100.0)

        if prob >= 75.0:
            level = "CRITICAL"
        elif prob >= 50.0:
            level = "HIGH"
        elif prob >= 25.0:
            level = "MODERATE"
        else:
            level = "LOW"

        info = RISK_LEVELS[level]

        # Extract top contributing factors using feature importances
        importances = self.model.feature_importances_
        feature_impact = []
        for feat, imp in zip(self.feature_columns, importances):
            val = feature_dict.get(feat, 0.0)
            feature_impact.append({"feature": feat, "importance": float(imp), "value": float(val)})

        feature_impact = sorted(feature_impact, key=lambda x: x["importance"], reverse=True)[:5]

        return {
            "prediction": pred,
            "probability_percent": round(prob, 1),
            "risk_level": level,
            "color": info["color"],
            "alert_stage": info["alert_stage"],
            "recommendation": info["action"],
            "icon": info["icon"],
            "top_drivers": feature_impact
        }
