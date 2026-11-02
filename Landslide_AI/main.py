#!/usr/bin/env python3
"""
Landslide_AI: Advanced Machine Learning & IoT Early Warning System
Main CLI Entry Point.
"""

import sys
import argparse
import subprocess
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    LOCATIONS,
    REGIONAL_MODEL_PATH,
    WSN_MODEL_PATH,
    SAMPLE_DATA_PATH,
)
from src.model import LandslidePredictor, WSNLandslidePredictor
from src.train import train_regional_model, train_wsn_model, update_model_metadata


def run_interactive_prediction():
    """
    Interactive terminal prompt for rapid landslide assessment.
    """
    print("\n" + "=" * 60)
    print("🌧️  AI LANDSLIDE RISK ASSESSMENT - INTERACTIVE CLI")
    print("=" * 60)

    print("\nSupported Locations:")
    for i, loc in enumerate(LOCATIONS, 1):
        print(f"  [{i}] {loc}")

    while True:
        loc_input = input("\nEnter location name or number: ").strip()
        if loc_input.isdigit() and 1 <= int(loc_input) <= len(LOCATIONS):
            location = LOCATIONS[int(loc_input) - 1]
            break
        elif loc_input in LOCATIONS:
            location = loc_input
            break
        else:
            print(f"❌ Invalid location. Please choose from: {', '.join(LOCATIONS)}")

    def get_float(prompt, min_val, max_val, default):
        while True:
            val_str = input(f"{prompt} [default {default}]: ").strip()
            if not val_str:
                return default
            try:
                val = float(val_str)
                if min_val <= val <= max_val:
                    return val
                print(f"❌ Value must be between {min_val} and {max_val}.")
            except ValueError:
                print("❌ Please enter a valid number.")

    rainfall = get_float("Enter 24h Rainfall (mm)", 0.0, 2000.0, 120.0)
    moisture = get_float("Enter Soil Moisture (%)", 0.0, 100.0, 75.0)
    slope = get_float("Enter Slope Angle (degrees)", 0.0, 90.0, 38.0)
    elevation = get_float("Enter Elevation (m)", 0.0, 9000.0, 1500.0)

    predictor = LandslidePredictor()
    result = predictor.predict_single(
        location=location,
        rainfall_mm=rainfall,
        soil_moisture_percent=moisture,
        slope_degree=slope,
        elevation_m=elevation,
    )

    print("\n" + "=" * 60)
    print("📊 RISK ASSESSMENT SUMMARY")
    print("=" * 60)
    print(f"Location               : {location}")
    print(f"Environmental Factors  : {rainfall} mm rain | {moisture}% moisture | {slope}° slope | {elevation}m elev")
    print(f"AI Risk Probability    : {result['probability_percent']:.1f}%")
    print(f"Risk Classification    : {result['icon']} {result['risk_level']}")
    print(f"Alert Stage            : {result['alert_stage']}")
    print(f"Factor of Safety (FS)  : {result['factor_of_safety']} ({'Stable' if result['is_geotechnically_stable'] else 'UNSTABLE'})")
    print(f"Recommended Action     : {result['recommendation']}")

    if result["triggers"]:
        print("\nPrimary Hazard Drivers:")
        for t in result["triggers"]:
            print(f"  • {t}")
    print("=" * 60 + "\n")


def run_batch_prediction(input_path: str, output_path: str):
    """
    Run batch inference on CSV dataset.
    """
    print(f"\n📂 Ingesting batch file: {input_path}")
    df = pd.read_csv(input_path)
    predictor = LandslidePredictor()
    results = predictor.predict_batch(df)
    results.to_csv(output_path, index=False)
    print(f"✅ Processed {len(results)} rows. Results saved to: {output_path}\n")


def launch_streamlit_app(port: int = 8501):
    """
    Launch the Streamlit web dashboard.
    """
    print(f"\n🌐 Launching Streamlit Dashboard on port {port}...")
    app_path = Path(__file__).resolve().parent / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", str(port)]
    subprocess.run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="Landslide_AI: Advanced Machine Learning & IoT Early Warning System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")

    # Command: train
    train_parser = subparsers.add_parser("train", help="Train AI prediction models")
    train_parser.add_argument(
        "--model", choices=["all", "regional", "wsn"], default="all", help="Model family to train"
    )
    train_parser.add_argument("--n-estimators", type=int, default=150, help="Number of estimators")
    train_parser.add_argument("--max-depth", type=int, default=12, help="Max depth of trees")

    # Command: predict
    pred_parser = subparsers.add_parser("predict", help="Predict landslide hazard for specific coordinates")
    pred_parser.add_argument("--location", type=str, default="Sikkim", help="Region/State name")
    pred_parser.add_argument("--rainfall", type=float, required=True, help="Rainfall in mm")
    pred_parser.add_argument("--moisture", type=float, required=True, help="Soil moisture in percent")
    pred_parser.add_argument("--slope", type=float, required=True, help="Slope angle in degrees")
    pred_parser.add_argument("--elevation", type=float, default=1500.0, help="Elevation in meters")

    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Batch process a CSV of sensor records")
    batch_parser.add_argument("--input", type=str, default=str(SAMPLE_DATA_PATH), help="Input CSV path")
    batch_parser.add_argument("--output", type=str, default="batch_predictions.csv", help="Output CSV path")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch Streamlit Web Dashboard")
    serve_parser.add_argument("--port", type=int, default=8501, help="Port to serve Streamlit app on")

    # Command: test
    subparsers.add_parser("test", help="Execute automated test suite")

    args = parser.parse_args()

    if args.command == "train":
        reg_m = {}
        wsn_m = {}
        if args.model in ["all", "regional"]:
            reg_m = train_regional_model(args.n_estimators, args.max_depth)
        if args.model in ["all", "wsn"]:
            wsn_m = train_wsn_model(args.n_estimators, args.max_depth)
        if args.model == "all":
            update_model_metadata(reg_m, wsn_m)

    elif args.command == "predict":
        predictor = LandslidePredictor()
        res = predictor.predict_single(
            location=args.location,
            rainfall_mm=args.rainfall,
            soil_moisture_percent=args.moisture,
            slope_degree=args.slope,
            elevation_m=args.elevation,
        )
        print("\n" + "=" * 50)
        print(f"Location       : {args.location}")
        print(f"Prediction     : {res['prediction_label']}")
        print(f"Probability    : {res['probability_percent']:.1f}%")
        print(f"Risk Level     : {res['icon']} {res['risk_level']}")
        print(f"Factor of Safety: {res['factor_of_safety']}")
        print(f"Recommendation : {res['recommendation']}")
        print("=" * 50 + "\n")

    elif args.command == "batch":
        run_batch_prediction(args.input, args.output)

    elif args.command == "serve":
        launch_streamlit_app(args.port)

    elif args.command == "test":
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
        subprocess.run(cmd)

    else:
        # No command specified: run interactive mode
        run_interactive_prediction()


if __name__ == "__main__":
    main()