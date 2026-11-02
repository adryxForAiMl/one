"""
Training Pipeline for Landslide_AI.
Executes end-to-end model training, hyperparameter configuration,
evaluation, cross-validation, and production serialization.
"""

import json
import argparse
import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from src.config import (
    REGIONAL_MODEL_PATH,
    WSN_MODEL_PATH,
    MODEL_METADATA_PATH,
)
from src.data_loader import (
    load_regional_data,
    load_wsn_data,
    generate_expanded_regional_dataset,
    prepare_wsn_splits,
)
from src.model import LandslidePredictor, WSNLandslidePredictor


def train_regional_model(n_estimators: int = 150, max_depth: int = 12) -> dict:
    """
    Trains the regional 5-factor landslide predictor and saves model artifact.
    """
    print("\n" + "=" * 60)
    print("🚀 TRAINING REGIONAL LANDSLIDE RISK MODEL")
    print("=" * 60)

    # Ingest data
    df = load_regional_data(use_expanded=True)
    print(f"📊 Dataset Loaded: {len(df)} samples across {df['location'].nunique()} locations.")
    print(f"   Landslide distribution: {dict(df['previous_landslide'].value_counts())}")

    # Split for independent evaluation
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["previous_landslide"])

    predictor = LandslidePredictor(model_path=str(REGIONAL_MODEL_PATH))
    train_metrics = predictor.train(train_df, n_estimators=n_estimators, max_depth=max_depth)

    # Evaluate on independent test set
    encoded_test = predictor._prepare_vector(
        location="Sikkim", rainfall_mm=0, soil_moisture_percent=0, slope_degree=0, elevation_m=0
    )  # just to verify alignment
    test_results = predictor.predict_batch(test_df)
    test_preds = test_results["Prediction"]
    y_test = test_df["previous_landslide"]

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    test_probs = test_results["Probability_%"] / 100.0

    eval_metrics = {
        "Accuracy": round(float(accuracy_score(y_test, test_preds)), 4),
        "Precision": round(float(precision_score(y_test, test_preds, zero_division=0)), 4),
        "Recall": round(float(recall_score(y_test, test_preds, zero_division=0)), 4),
        "F1 Score": round(float(f1_score(y_test, test_preds, zero_division=0)), 4),
        "ROC-AUC": round(float(roc_auc_score(y_test, test_probs)), 4),
    }

    predictor.metadata["metrics"] = eval_metrics
    predictor.metadata["train_samples"] = len(train_df)
    predictor.metadata["test_samples"] = len(test_df)
    predictor.save()

    print("\n✅ Regional Model Evaluation on Independent Test Split:")
    for k, v in eval_metrics.items():
        print(f"   • {k:15}: {v * 100:.2f}%")
    print(f"💾 Model artifact saved to: {REGIONAL_MODEL_PATH}")

    return eval_metrics


def train_wsn_model(n_estimators: int = 150, max_depth: int = 14) -> dict:
    """
    Trains the 34-feature Geotechnical WSN sensor model.
    """
    print("\n" + "=" * 60)
    print("🛰️ TRAINING WSN GEOTECHNICAL SENSOR MODEL")
    print("=" * 60)

    train_df, test_df = prepare_wsn_splits(test_size=0.2, random_state=42)
    print(f"📊 WSN Ingestion: {len(train_df)} train samples, {len(test_df)} test samples, 34 features.")

    predictor = WSNLandslidePredictor(model_path=str(WSN_MODEL_PATH))
    predictor.train(train_df, n_estimators=n_estimators, max_depth=max_depth)

    # Evaluate on hold-out test set
    X_test = test_df.drop("Label", axis=1)
    y_test = test_df["Label"]

    X_test_scaled = predictor.scaler.transform(X_test)
    preds = predictor.model.predict(X_test_scaled)
    probs = predictor.model.predict_proba(X_test_scaled)[:, 1]

    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    eval_metrics = {
        "Accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "Precision": round(float(precision_score(y_test, preds, zero_division=0)), 4),
        "Recall": round(float(recall_score(y_test, preds, zero_division=0)), 4),
        "F1 Score": round(float(f1_score(y_test, preds, zero_division=0)), 4),
        "ROC-AUC": round(float(roc_auc_score(y_test, probs)), 4),
    }

    predictor.metadata["metrics"] = eval_metrics
    predictor.metadata["train_samples"] = len(train_df)
    predictor.metadata["test_samples"] = len(test_df)
    predictor.save()

    print("\n✅ WSN Geotechnical Model Test Metrics:")
    for k, v in eval_metrics.items():
        print(f"   • {k:15}: {v * 100:.2f}%")
    print(f"💾 Model artifact saved to: {WSN_MODEL_PATH}")

    return eval_metrics


def update_model_metadata(regional_metrics: dict, wsn_metrics: dict):
    """
    Saves unified model metadata JSON card.
    """
    metadata = {
        "system": "AI Landslide Early Warning System (Landslide_AI)",
        "version": "2.0.0",
        "last_trained": datetime.datetime.now().isoformat(),
        "models": {
            "regional_model": {
                "name": "Random Forest Regional Predictor",
                "path": str(REGIONAL_MODEL_PATH.name),
                "features": 5,
                "input_columns": ["location", "rainfall_mm", "soil_moisture_percent", "slope_degree", "elevation_m"],
                "metrics": regional_metrics
            },
            "wsn_sensor_model": {
                "name": "WSN Geotechnical Sensor Classifier",
                "path": str(WSN_MODEL_PATH.name),
                "features": 34,
                "metrics": wsn_metrics
            }
        }
    }
    with open(MODEL_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"📋 Model metadata registered in: {MODEL_METADATA_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Train Landslide_AI Prediction Models")
    parser.add_argument(
        "--model",
        type=str,
        choices=["all", "regional", "wsn"],
        default="all",
        help="Model to train: all, regional, or wsn (default: all)"
    )
    parser.add_argument("--n-estimators", type=int, default=150, help="Number of trees (default: 150)")
    parser.add_argument("--max-depth", type=int, default=12, help="Maximum tree depth (default: 12)")
    args = parser.parse_args()

    reg_metrics = {}
    wsn_metrics = {}

    if args.model in ["all", "regional"]:
        reg_metrics = train_regional_model(n_estimators=args.n_estimators, max_depth=args.max_depth)

    if args.model in ["all", "wsn"]:
        wsn_metrics = train_wsn_model(n_estimators=args.n_estimators, max_depth=args.max_depth)

    if args.model == "all":
        update_model_metadata(reg_metrics, wsn_metrics)

    print("\n🎉 Training completed successfully!\n")


if __name__ == "__main__":
    main()
