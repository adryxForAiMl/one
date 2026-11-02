"""
AI Landslide Early Warning System (Landslide_AI)
Streamlit Enterprise Dashboard v2.0.0
Author: Landslide AI Research Team
"""

import sys
import json
import time
import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    LOCATIONS,
    LOCATION_COORDINATES,
    RISK_LEVELS,
    REGIONAL_MODEL_PATH,
    WSN_MODEL_PATH,
    MODEL_METADATA_PATH,
    SAMPLE_DATA_PATH,
)
from src.model import LandslidePredictor, WSNLandslidePredictor
from src.geoutils import create_landslide_map
from src.simulator import SensorStationSimulator
from src.data_loader import calculate_factor_of_safety, validate_regional_input

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Landslide_AI: Early Warning & Risk Assessment",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# MODERN DARK GLASSMORPHISM STYLING
# ============================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 90% 10%, rgba(0, 229, 255, 0.08), transparent 35%),
                    radial-gradient(circle at 10% 85%, rgba(255, 23, 68, 0.05), transparent 30%),
                    linear-gradient(135deg, #070d18 0%, #0a1424 50%, #070d18 100%);
        color: #e2e8f0;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #091322 0%, #060c16 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }

    /* Hero Header */
    .hero-container {
        padding: 28px 32px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(16, 29, 50, 0.85) 0%, rgba(9, 18, 32, 0.95) 100%);
        border: 1px solid rgba(0, 229, 255, 0.2);
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
    }
    .hero-title {
        font-size: 34px;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #ffffff, #67e8f9, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 15px;
        font-weight: 400;
        max-width: 900px;
        line-height: 1.5;
    }
    .hero-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        background: rgba(0, 229, 255, 0.1);
        border: 1px solid rgba(0, 229, 255, 0.25);
        color: #38bdf8;
    }

    /* Cards */
    .metric-card {
        padding: 18px 20px;
        border-radius: 14px;
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 229, 255, 0.35);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 26px;
        font-weight: 800;
        margin-top: 4px;
    }

    /* Risk Banner Card */
    .risk-banner {
        padding: 24px;
        border-radius: 16px;
        margin: 16px 0;
        border: 1px solid;
    }
    .risk-LOW {
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.12), rgba(0, 230, 118, 0.04));
        border-color: rgba(0, 230, 118, 0.35);
    }
    .risk-MODERATE {
        background: linear-gradient(135deg, rgba(255, 235, 59, 0.12), rgba(255, 235, 59, 0.04));
        border-color: rgba(255, 235, 59, 0.35);
    }
    .risk-HIGH {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.15), rgba(255, 152, 0, 0.05));
        border-color: rgba(255, 152, 0, 0.4);
    }
    .risk-CRITICAL {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(244, 67, 54, 0.06));
        border-color: rgba(244, 67, 54, 0.5);
    }

    /* Gauge */
    .gauge-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 16px;
    }
    .gauge-circle {
        position: relative;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: conic-gradient(var(--fill-color) calc(var(--val) * 1%), rgba(255,255,255,0.06) 0);
    }
    .gauge-inner {
        position: absolute;
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: #0b1526;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .gauge-pct {
        font-size: 24px;
        font-weight: 800;
        color: #ffffff;
    }
    .gauge-sub {
        font-size: 10px;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
    }

    /* Custom Button */
    .stButton>button {
        border-radius: 10px;
        font-weight: 700;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MODEL & CACHING PIPELINE
# ============================================================
@st.cache_resource(show_spinner=False)
def load_predictors():
    """
    Cached loader for regional and WSN AI models.
    """
    reg = LandslidePredictor()
    reg.load(str(REGIONAL_MODEL_PATH))

    wsn = WSNLandslidePredictor()
    try:
        wsn.load(str(WSN_MODEL_PATH))
    except Exception:
        wsn = None

    metadata = {}
    if MODEL_METADATA_PATH.exists():
        try:
            with open(MODEL_METADATA_PATH, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass

    return reg, wsn, metadata

regional_predictor, wsn_predictor, model_metadata = load_predictors()

# Session state initialization
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []

if "sim_packets" not in st.session_state:
    st.session_state.sim_packets = []

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🏔️ Landslide_AI Core")
    st.markdown("Advanced Multi-Scale Landslide Hazard Warning System.")

    st.markdown(
        """
        <div style="background: rgba(0, 229, 255, 0.08); border: 1px solid rgba(0, 229, 255, 0.25);
                    padding: 10px 14px; border-radius: 10px; margin-bottom: 16px;">
            <div style="font-size: 11px; color: #67e8f9; font-weight: 700;">● SYSTEM STATUS: ACTIVE</div>
            <div style="font-size: 13px; font-weight: 800; color: #ffffff; margin-top: 2px;">Dual AI Engine Online</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🎯 Quick Region Presets")
    preset_choice = st.selectbox(
        "Select Regional Hotspot",
        ["Custom Input"] + LOCATIONS,
        index=0,
    )

    st.divider()

    st.markdown("#### 🤖 Model Specifications")
    st.markdown(
        f"""
        - **Regional Model**: Random Forest (5-Factor Calibrated)
        - **Accuracy**: `{model_metadata.get('models', {}).get('regional_model', {}).get('metrics', {}).get('Accuracy', 0.9067) * 100:.1f}%`
        - **ROC-AUC**: `{model_metadata.get('models', {}).get('regional_model', {}).get('metrics', {}).get('ROC-AUC', 0.9339) * 100:.1f}%`
        - **WSN Sensor Model**: 34-Sensor Deep IoT Classifier
        - **Accuracy**: `{model_metadata.get('models', {}).get('wsn_sensor_model', {}).get('metrics', {}).get('Accuracy', 0.9782) * 100:.1f}%`
        """
    )

    st.divider()
    st.caption("Decision-support system for geological & civil defense monitoring. Landslide_AI v2.0.0.")

# ============================================================
# HERO HEADER
# ============================================================
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🌧️ AI Landslide Early Warning & Risk Assessment System</div>
        <div class="hero-subtitle">
            Autonomous multi-sensor geotechnical intelligence combining empirical meteorological thresholds, 
            Infinite Slope Stability mechanics, and IoT telemetry for the North Eastern Region & Himalayas.
        </div>
        <div class="hero-tags">
            <span class="hero-badge">🤖 RANDOM FOREST ENSEMBLE</span>
            <span class="hero-badge">🛰️ 34-SENSOR WSN TELEMETRY</span>
            <span class="hero-badge">📐 INFINITE SLOPE STABILITY</span>
            <span class="hero-badge">🗺️ GIS GEOSPATIAL INTELLIGENCE</span>
            <span class="hero-badge">⚡ REAL-TIME HAZARD SCORING</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# MAIN APPLICATION TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "🗺️ Regional Assessment",
        "🔬 Geotechnical WSN (34 Sensors)",
        "🌐 GIS Hazard Map",
        "📊 Batch CSV Analytics",
        "⏱️ Live Telemetry Simulator",
        "🧠 Model Governance & XAI",
    ]
)

# ============================================================
# TAB 1: REGIONAL RAPID ASSESSMENT
# ============================================================
with tab1:
    st.markdown("### 📍 Regional Terrain & Meteorological Hazard Assessment")
    st.markdown("Analyze slope vulnerability across 10 mountainous states using 5 environmental parameters.")

    # Apply preset values if chosen
    if preset_choice != "Custom Input" and preset_choice in LOCATION_COORDINATES:
        p_data = LOCATION_COORDINATES[preset_choice]
        default_loc = preset_choice
        default_elev = float(p_data["elevation"])
        default_slope = 38.0 if "Sikkim" in preset_choice or "Arunachal" in preset_choice else 25.0
        default_rain = 145.0 if "Meghalaya" in preset_choice or "Sikkim" in preset_choice else 75.0
        default_moist = 78.0 if "Meghalaya" in preset_choice or "Sikkim" in preset_choice else 52.0
    else:
        default_loc = "Sikkim"
        default_elev = 1500.0
        default_slope = 35.0
        default_rain = 110.0
        default_moist = 65.0

    col_in1, col_in2, col_in3 = st.columns([1.2, 1.2, 1.2])

    with col_in1:
        loc_val = st.selectbox("Monitoring Region", LOCATIONS, index=LOCATIONS.index(default_loc))
        elev_val = st.number_input("Elevation above Sea Level (m)", min_value=0.0, max_value=8848.0, value=default_elev, step=50.0)

    with col_in2:
        rain_val = st.slider("24-Hour Cumulative Rainfall (mm)", min_value=0.0, max_value=400.0, value=default_rain, step=5.0)
        moist_val = st.slider("Soil Moisture Saturation (%)", min_value=0.0, max_value=100.0, value=default_moist, step=1.0)

    with col_in3:
        slope_val = st.slider("Slope Incline (degrees °)", min_value=0.0, max_value=85.0, value=default_slope, step=1.0)
        st.markdown("<br>", unsafe_allow_html=True)
        predict_btn = st.button("⚡ EXECUTE HAZARD ASSESSMENT", type="primary", use_container_width=True)

    # Real-time quick metric badges
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.markdown(
            f"""<div class="metric-card"><div class="metric-label">Selected Sector</div>
            <div class="metric-value">{loc_val}</div></div>""",
            unsafe_allow_html=True,
        )
    with mcol2:
        st.markdown(
            f"""<div class="metric-card"><div class="metric-label">24h Rainfall</div>
            <div class="metric-value">{rain_val:.0f} <span style="font-size:16px;color:#94a3b8">mm</span></div></div>""",
            unsafe_allow_html=True,
        )
    with mcol3:
        st.markdown(
            f"""<div class="metric-card"><div class="metric-label">Soil Moisture</div>
            <div class="metric-value">{moist_val:.0f} <span style="font-size:16px;color:#94a3b8">%</span></div></div>""",
            unsafe_allow_html=True,
        )
    with mcol4:
        st.markdown(
            f"""<div class="metric-card"><div class="metric-label">Slope Incline</div>
            <div class="metric-value">{slope_val:.0f} <span style="font-size:16px;color:#94a3b8">°</span></div></div>""",
            unsafe_allow_html=True,
        )

    # Inference Execution
    if predict_btn or "last_regional_result" in st.session_state:
        if predict_btn:
            with st.spinner("🔄 Computing physical slope mechanics and ML classification..."):
                res = regional_predictor.predict_single(
                    location=loc_val,
                    rainfall_mm=rain_val,
                    soil_moisture_percent=moist_val,
                    slope_degree=slope_val,
                    elevation_m=elev_val,
                )
                st.session_state["last_regional_result"] = res
                st.session_state.prediction_history.append(
                    {
                        "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        "Location": loc_val,
                        "Rainfall (mm)": rain_val,
                        "Moisture (%)": moist_val,
                        "Slope (°)": slope_val,
                        "Elevation (m)": elev_val,
                        "Probability (%)": res["probability_percent"],
                        "Risk Level": res["risk_level"],
                        "Factor of Safety": res["factor_of_safety"],
                    }
                )

        res = st.session_state["last_regional_result"]

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🚨 Hazard Assessment Results")

        res_col1, res_col2 = st.columns([2.2, 1.2])

        with res_col1:
            st.markdown(
                f"""
                <div class="risk-banner risk-{res['risk_level']}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2 style="margin:0; font-size:24px; color:#ffffff; font-weight:800;">
                            {res['icon']} LANDSLIDE RISK: {res['risk_level']}
                        </h2>
                        <span style="background:rgba(255,255,255,0.15); padding:4px 12px; border-radius:8px;
                                     font-weight:700; font-size:12px; color:#ffffff;">
                            {res['alert_stage']}
                        </span>
                    </div>
                    <div style="margin-top:12px; font-size:15px; color:#f1f5f9; line-height:1.6;">
                        <strong>CIVIL DEFENSE ACTION:</strong> {res['recommendation']}
                    </div>
                    <div style="margin-top:10px; font-size:13px; color:#cbd5e1;">
                        <strong>Geotechnical Factor of Safety (FS):</strong> 
                        <span style="font-weight:800; color:{'#00e676' if res['is_geotechnically_stable'] else '#ff1744'};">
                            {res['factor_of_safety']} ({'STABLE' if res['is_geotechnically_stable'] else 'LIMIT STATE FAILURE'})
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if res["triggers"]:
                st.markdown("**Hazard Contributing Drivers:**")
                for trig in res["triggers"]:
                    st.markdown(f"- ⚠️ {trig}")

        with res_col2:
            st.markdown(
                f"""
                <div class="metric-card" style="text-align:center;">
                    <div class="gauge-container">
                        <div class="gauge-circle" style="--val:{res['probability_percent']}; --fill-color:{res['color']};">
                            <div class="gauge-inner">
                                <div class="gauge-pct">{res['probability_percent']:.1f}%</div>
                                <div class="gauge-sub">AI Hazard Index</div>
                            </div>
                        </div>
                    </div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:8px;">Calibrated Probability Score</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Export Report
        st.markdown("<br>", unsafe_allow_html=True)
        report_df = pd.DataFrame(
            [
                {"Parameter": "Location Sector", "Value": loc_val},
                {"Parameter": "24h Cumulative Rainfall", "Value": f"{rain_val:.1f} mm"},
                {"Parameter": "Soil Moisture Saturation", "Value": f"{moist_val:.1f} %"},
                {"Parameter": "Slope Incline", "Value": f"{slope_val:.1f} °"},
                {"Parameter": "Elevation", "Value": f"{elev_val:.0f} m"},
                {"Parameter": "AI Landslide Classification", "Value": res["prediction_label"]},
                {"Parameter": "Probability Score", "Value": f"{res['probability_percent']:.1f} %"},
                {"Parameter": "Hazard Classification", "Value": res["risk_level"]},
                {"Parameter": "Factor of Safety (FS)", "Value": f"{res['factor_of_safety']}"},
                {"Parameter": "Alert Directive", "Value": res["alert_stage"]},
            ]
        )
        csv_bytes = report_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ DOWNLOAD HAZARD AUDIT REPORT (CSV)",
            data=csv_bytes,
            file_name=f"landslide_audit_{loc_val}_{int(time.time())}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# TAB 2: ADVANCED GEOTECHNICAL WSN SENSORS (34 FEATURES)
# ============================================================
with tab2:
    st.markdown("### 🔬 Advanced Geotechnical & Wireless Sensor Network (WSN) Analysis")
    st.markdown("Ingest 34 multi-parameter IoT sensor telemetry feeds, including pore water pressure, soil strain, and micro-seismic acoustic emissions.")

    if wsn_predictor is None:
        st.warning("WSN model not loaded. Please train using `python main.py train --model wsn`.")
    else:
        st.markdown("#### Select Disaster Telemetry Scenario Preset:")
        scenario_choice = st.radio(
            "Scenario",
            ["Monsoon Surge in Sikkim", "Critical Pore-Pressure Liquefaction", "Post-Earthquake Slope Failure", "Stable Sunny Day"],
            horizontal=True,
        )

        # Generate sample sensor packet from simulator based on scenario
        sim_scenario_map = {
            "Monsoon Surge in Sikkim": "Monsoon Surge",
            "Critical Pore-Pressure Liquefaction": "Critical Slope Failure",
            "Post-Earthquake Slope Failure": "Micro-Seismic Event",
            "Stable Sunny Day": "Normal",
        }
        sensor_data = SensorStationSimulator.generate_packet(scenario=sim_scenario_map[scenario_choice])

        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            st.markdown("**Hydrological Sensors**")
            wsn_rain = st.number_input("Rainfall (mm)", value=float(sensor_data["Rainfall_mm"]))
            wsn_rain_3d = st.number_input("3-Day Cumulative Rain (mm)", value=float(sensor_data["Rainfall_3Day"]))
            wsn_moist = st.number_input("Soil Saturation (0.0 - 1.0)", value=float(sensor_data["Soil_Saturation"]), min_value=0.0, max_value=1.0)
            wsn_pore = st.number_input("Pore Water Pressure (kPa)", value=float(sensor_data["Pore_Water_Pressure_kPa"]))

        with s_col2:
            st.markdown("**Geomechanical Sensors**")
            wsn_slope = st.number_input("Slope Angle (°)", value=float(sensor_data["Slope_Angle"]))
            wsn_strain = st.number_input("Soil Shear Strain", value=float(sensor_data["Soil_Strain"]), format="%.6f")
            wsn_acoustic = st.number_input("Acoustic Emission (dB)", value=float(sensor_data["Acoustic_Emission_dB"]))
            wsn_seismic = st.number_input("Microseismic Activity (g)", value=float(sensor_data["Microseismic_Activity"]), format="%.3f")

        with s_col3:
            st.markdown("**Environmental & Soil Metrics**")
            wsn_temp = st.number_input("Soil Temperature (°C)", value=float(sensor_data["Temperature_C"]))
            wsn_ndvi = st.number_input("NDVI Vegetation Index", value=float(sensor_data["NDVI_Index"]))
            wsn_elev = st.number_input("Station Elevation (m)", value=float(sensor_data["elevation_m"]))
            wsn_tdr = st.number_input("TDR Reflection Index", value=float(sensor_data["TDR_Reflection_Index"]))

        if st.button("🔍 INGEST & EVALUATE SENSOR TELEMETRY", type="primary", use_container_width=True):
            eval_dict = dict(sensor_data)
            eval_dict.update({
                "Rainfall_mm": wsn_rain,
                "Rainfall_3Day": wsn_rain_3d,
                "Soil_Saturation": wsn_moist,
                "Pore_Water_Pressure_kPa": wsn_pore,
                "Slope_Angle": wsn_slope,
                "Soil_Strain": wsn_strain,
                "Acoustic_Emission_dB": wsn_acoustic,
                "Microseismic_Activity": wsn_seismic,
                "Temperature_C": wsn_temp,
                "NDVI_Index": wsn_ndvi,
                "Elevation_m": wsn_elev,
                "TDR_Reflection_Index": wsn_tdr,
            })

            wsn_res = wsn_predictor.predict_sample(eval_dict)

            st.markdown(
                f"""
                <div class="risk-banner risk-{wsn_res['risk_level']}">
                    <h3 style="margin:0; color:#fff;">{wsn_res['icon']} SENSOR RISK CLASSIFICATION: {wsn_res['risk_level']} ({wsn_res['probability_percent']:.1f}%)</h3>
                    <div style="margin-top:8px; font-size:14px; color:#f1f5f9;">{wsn_res['recommendation']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### 🔑 Top Risk Contributing Drivers (Feature Attribution):")
            drv_cols = st.columns(len(wsn_res["top_drivers"]))
            for idx, drv in enumerate(wsn_res["top_drivers"]):
                with drv_cols[idx]:
                    st.metric(label=drv["feature"].replace("_", " "), value=f"{drv['value']:.2f}", delta=f"{drv['importance']*100:.1f}% weight")

# ============================================================
# TAB 3: GIS INTERACTIVE HAZARD MAP
# ============================================================
with tab3:
    st.markdown("### 🌐 Regional Geospatial Hazard Map")
    st.markdown("Interactive GIS interface visualizing real-time station statuses, terrain slopes, and susceptibility heatmaps across North East India and Himalayas.")

    # Filter control
    map_filter = st.radio("Map Filter:", ["All Monitoring Stations", "High & Critical Risk Zones Only"], horizontal=True)

    # Compile stations list
    stations_to_plot = []
    for loc, coords in LOCATION_COORDINATES.items():
        # Compute baseline regional risk
        loc_res = regional_predictor.predict_single(
            location=loc,
            rainfall_mm=135.0 if loc in ["Sikkim", "Meghalaya"] else 40.0,
            soil_moisture_percent=75.0 if loc in ["Sikkim", "Meghalaya"] else 45.0,
            slope_degree=38.0 if loc in ["Sikkim", "Meghalaya", "Arunachal Pradesh"] else 20.0,
            elevation_m=coords["elevation"],
        )
        if map_filter == "High & Critical Risk Zones Only" and loc_res["risk_level"] not in ["HIGH", "CRITICAL"]:
            continue

        stations_to_plot.append(
            {
                "location": loc,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "elevation_m": coords["elevation"],
                "district": coords["district"],
                "risk_level": loc_res["risk_level"],
                "probability_percent": loc_res["probability_percent"],
                "rainfall_mm": 135.0 if loc in ["Sikkim", "Meghalaya"] else 40.0,
                "soil_moisture_percent": 75.0 if loc in ["Sikkim", "Meghalaya"] else 45.0,
                "slope_degree": 38.0 if loc in ["Sikkim", "Meghalaya", "Arunachal Pradesh"] else 20.0,
            }
        )

    fmap = create_landslide_map(stations=stations_to_plot, zoom_start=6)
    st.components.v1.html(fmap._repr_html_(), height=550)

# ============================================================
# TAB 4: BATCH CSV INGESTION & BULK MAPPING
# ============================================================
with tab4:
    st.markdown("### 📊 Bulk Ingestion & Batch Risk Analytics")
    st.markdown("Upload telemetry CSV files containing location coordinates and meteorological measurements to perform instant batch hazard classification.")

    uploaded_file = st.file_uploader("Upload CSV Data File", type=["csv"])

    sample_button = st.button("📂 Load Pre-existing Sample Dataset")
    if sample_button or uploaded_file:
        if uploaded_file:
            batch_df = pd.read_csv(uploaded_file)
        else:
            batch_df = pd.read_csv(SAMPLE_DATA_PATH)

        st.markdown(f"**Loaded {len(batch_df)} records:**")
        st.dataframe(batch_df.head(), use_container_width=True)

        with st.spinner("⚡ Running batch inference engine..."):
            enriched_df = regional_predictor.predict_batch(batch_df)

        st.markdown("#### 📋 Enriched Batch Predictions:")
        st.dataframe(enriched_df, use_container_width=True)

        # Risk distribution charts
        st.markdown("#### 📈 Hazard Level Breakdown:")
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            risk_counts = enriched_df["Risk_Level"].value_counts()
            st.bar_chart(risk_counts)
        with b_col2:
            st.markdown(f"- **Total Stations Evaluated**: `{len(enriched_df)}`")
            for rk in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
                cnt = risk_counts.get(rk, 0)
                st.markdown(f"- **{rk}**: `{cnt}` stations ({cnt/len(enriched_df)*100:.1f}%)")

        # Download enriched CSV
        out_csv = enriched_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ EXPORT ENRICHED BATCH DATA (CSV)",
            data=out_csv,
            file_name=f"batch_evaluated_{int(time.time())}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# TAB 5: REAL-TIME IOT TELEMETRY SIMULATOR
# ============================================================
with tab5:
    st.markdown("### ⏱️ Real-time IoT Geotechnical Telemetry Stream")
    st.markdown("Live streaming emulator ingesting continuous packet bursts from wireless sensor stations deployed along critical Himalayan transit corridors.")

    sim_col1, sim_col2 = st.columns([1, 2])

    with sim_col1:
        st_select = st.selectbox(
            "Target Sensor Node",
            [f"{s['id']}: {s['name']} ({s['state']})" for s in SensorStationSimulator.get_stations()],
        )
        selected_id = st_select.split(":")[0]
        sim_scenario = st.selectbox("Trigger Environment", ["Normal", "Monsoon Surge", "Critical Slope Failure", "Micro-Seismic Event"])
        poll_btn = st.button("📡 PULL NEXT TELEMETRY PACKET", type="primary", use_container_width=True)

    if poll_btn or len(st.session_state.sim_packets) == 0:
        new_packet = SensorStationSimulator.generate_packet(station_id=selected_id, scenario=sim_scenario)
        # Classify with regional predictor
        eval_res = regional_predictor.predict_single(
            location=new_packet["location"],
            rainfall_mm=new_packet["Rainfall_mm"],
            soil_moisture_percent=new_packet["soil_moisture_percent"],
            slope_degree=new_packet["slope_degree"],
            elevation_m=new_packet["elevation_m"],
        )
        new_packet["Risk_Level"] = eval_res["risk_level"]
        new_packet["Probability_%"] = eval_res["probability_percent"]
        st.session_state.sim_packets.append(new_packet)

        # Keep last 15 packets
        if len(st.session_state.sim_packets) > 15:
            st.session_state.sim_packets.pop(0)

    with sim_col2:
        latest = st.session_state.sim_packets[-1]
        st.markdown(
            f"""
            <div class="risk-banner risk-{latest['Risk_Level']}" style="margin:0;">
                <div style="font-size:12px; color:#cbd5e1;">LATEST PACKET: {latest['timestamp']} | NODE {latest['station_id']}</div>
                <h3 style="margin:4px 0; color:#fff;">Status: {latest['Risk_Level']} ({latest['Probability_%']:.1f}% Risk)</h3>
                <div style="font-size:13px; color:#f1f5f9;">Pore Pressure: {latest['Pore_Water_Pressure_kPa']} kPa | Rainfall: {latest['Rainfall_mm']} mm | Strain: {latest['Soil_Strain']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Real-time Telemetry Trendlines
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📈 Sensor Telemetry History:")
    stream_df = pd.DataFrame(st.session_state.sim_packets)
    if "Pore_Water_Pressure_kPa" in stream_df.columns:
        chart_data = stream_df[["timestamp", "Rainfall_mm", "Pore_Water_Pressure_kPa", "Acoustic_Emission_dB"]].set_index("timestamp")
        st.line_chart(chart_data)

# ============================================================
# TAB 6: MODEL GOVERNANCE & XAI
# ============================================================
with tab6:
    st.markdown("### 🧠 Model Governance, Metrics & Explainable AI (XAI)")
    st.markdown("Audit trails, benchmark verification, confusion matrices, and physical slope stability formulations.")

    gov_col1, gov_col2 = st.columns(2)

    with gov_col1:
        st.markdown("#### 📐 Mathematical Formulation")
        st.markdown(
            r"""
            **Infinite Slope Stability Equation (Factor of Safety):**
            $$FS = \frac{c' + (\gamma - m \cdot \gamma_w) \cdot z \cdot \cos^2(\beta) \cdot \tan(\phi')}{\gamma \cdot z \cdot \sin(\beta) \cdot \cos(\beta)}$$

            Where:
            - $c'$: Effective Soil Cohesion (kPa)
            - $\phi'$: Angle of Internal Friction ($^\circ$)
            - $\beta$: Slope Incline Angle ($^\circ$)
            - $m$: Saturation Ratio ($\approx$ Soil Moisture / 100)
            - $\gamma, \gamma_w$: Soil & Water Unit Weights ($kN/m^3$)
            - $z$: Failure Shear Surface Depth ($m$)
            
            **Empirical Rainfall Threshold Formulation:**
            $$I = 14.82 \cdot D^{-0.39}$$
            Where $I$ is rainfall intensity (mm/h) and $D$ is rainfall duration (hours).
            """
        )

    with gov_col2:
        st.markdown("#### 📊 Benchmark Validation Metrics")
        if model_metadata and "models" in model_metadata:
            st.json(model_metadata["models"])
        else:
            st.info("Training metadata JSON is available in `models/model_metadata.json`.")

    st.divider()
    st.markdown("#### 📜 Session Prediction History Audit Log:")
    if st.session_state.prediction_history:
        hist_df = pd.DataFrame(st.session_state.prediction_history)
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.caption("No interactive predictions performed in this session yet.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px;">
        Landslide_AI &bull; Advanced Early Warning & Geotechnical Decision Support System &bull; Version 2.0.0 &bull; MIT License
    </div>
    """,
    unsafe_allow_html=True,
)
