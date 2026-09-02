import streamlit as st
import pandas as pd
import joblib


st.set_page_config(
    page_title="AI Landslide Early Warning System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


MODEL_PATH = "models/landslide_model.pkl"


LOCATIONS = [
    "Sikkim",
    "Arunachal Pradesh",
    "Assam",
    "Meghalaya",
    "Nagaland",
    "Mizoram",
    "Tripura"
]


FEATURE_NAMES = [
    "rainfall_mm",
    "soil_moisture_percent",
    "slope_degree",
    "elevation_m",
    "location_Arunachal Pradesh",
    "location_Assam",
    "location_Meghalaya",
    "location_Mizoram",
    "location_Nagaland",
    "location_Sikkim",
    "location_Tripura"
]


@st.cache_resource
def load_model():
    model_data = joblib.load(MODEL_PATH)

    if not isinstance(model_data, dict):
        raise ValueError(
            "The saved model file does not contain the expected dictionary structure."
        )

    if "model" not in model_data:
        raise ValueError(
            "The saved model file does not contain the 'model' key."
        )

    if "features" not in model_data:
        raise ValueError(
            "The saved model file does not contain the 'features' key."
        )

    trained_model = model_data["model"]
    trained_features = model_data["features"]

    if not trained_features:
        raise ValueError(
            "The trained feature list is empty."
        )

    return trained_model, trained_features


def create_input_data(
    location,
    rainfall,
    soil_moisture,
    slope,
    elevation,
    feature_names
):
    data = pd.DataFrame({
        "location": [location],
        "rainfall_mm": [rainfall],
        "soil_moisture_percent": [soil_moisture],
        "slope_degree": [slope],
        "elevation_m": [elevation]
    })

    data = pd.get_dummies(
        data,
        columns=["location"]
    )

    data = data.reindex(
        columns=feature_names,
        fill_value=0
    )

    data = data.astype(float)

    return data


def get_risk_level(prediction, probability):
    if prediction == 0:
        if probability >= 0.40:
            return "MODERATE", "🟡"
        return "LOW", "🟢"

    if probability >= 0.90:
        return "CRITICAL", "🔴"

    if probability >= 0.70:
        return "HIGH", "🟠"

    return "MODERATE", "🟡"


def get_environmental_analysis(
    rainfall,
    soil_moisture,
    slope,
    elevation
):
    observations = []

    if rainfall >= 200:
        observations.append("🌧️ Very high rainfall input")
    elif rainfall >= 100:
        observations.append("🌦️ High rainfall input")
    elif rainfall >= 50:
        observations.append("🌦️ Moderate rainfall input")
    else:
        observations.append("☀️ Relatively low rainfall input")

    if soil_moisture >= 80:
        observations.append("💧 Very high soil moisture")
    elif soil_moisture >= 60:
        observations.append("💧 High soil moisture")
    elif soil_moisture >= 40:
        observations.append("🌱 Moderate soil moisture")
    else:
        observations.append("🌱 Relatively low soil moisture")

    if slope >= 40:
        observations.append("⛰️ Very steep terrain")
    elif slope >= 25:
        observations.append("⛰️ Steep terrain")
    elif slope >= 15:
        observations.append("⛰️ Moderate slope")
    else:
        observations.append("🏞️ Relatively gentle slope")

    if elevation >= 2000:
        observations.append("🏔️ High elevation")
    elif elevation >= 1000:
        observations.append("🏔️ Moderate elevation")
    else:
        observations.append("🌄 Lower elevation")

    return observations


def get_recommendation(risk_level):
    if risk_level == "CRITICAL":
        return (
            "Immediate attention is recommended. "
            "Monitor the location closely and follow official local "
            "disaster-management warnings and evacuation instructions."
        )

    if risk_level == "HIGH":
        return (
            "Conditions indicate elevated landslide risk. "
            "Increase monitoring and remain alert to local weather "
            "and official warnings."
        )

    if risk_level == "MODERATE":
        return (
            "Conditions indicate a moderate level of concern. "
            "Continue monitoring rainfall, soil moisture and terrain conditions."
        )

    return (
        "Current input conditions indicate relatively low risk "
        "according to the trained model. Continue normal monitoring."
    )


try:
    model, model_features = load_model()

except Exception as error:
    st.error("Unable to load the trained landslide model.")
    st.code(str(error))
    st.stop()


st.title("🌍 AI-Based Landslide Early Warning System")
st.subheader("North Eastern Region (NER)")

st.write(
    "An interactive machine-learning system for estimating "
    "landslide risk using environmental and geographic conditions."
)


with st.sidebar:
    st.header("🛰️ System Information")

    st.write(
        "This application uses a trained Random Forest machine-learning "
        "model to classify landslide risk."
    )

    st.divider()

    st.header("📍 Supported Locations")

    for location_name in LOCATIONS:
        st.write(f"• {location_name}")

    st.divider()

    st.header("🤖 Model Information")

    st.write("Algorithm: Random Forest")
    st.write(f"Input Features: {len(model_features)}")
    st.write("Prediction Type: Binary Classification")


st.divider()

st.header("📊 Environmental Condition Analysis")

st.write(
    "Enter the current environmental conditions to generate "
    "an AI-based landslide-risk prediction."
)


left_column, right_column = st.columns(2)


with left_column:

    st.subheader("📍 Geographic Information")

    location = st.selectbox(
        "Select Location",
        LOCATIONS,
        index=0
    )

    elevation = st.number_input(
        "Elevation (m)",
        min_value=0.0,
        max_value=10000.0,
        value=1000.0,
        step=50.0
    )


with right_column:

    st.subheader("🌧️ Environmental Conditions")

    rainfall = st.number_input(
        "Rainfall (mm)",
        min_value=0.0,
        max_value=5000.0,
        value=100.0,
        step=10.0
    )

    soil_moisture = st.number_input(
        "Soil Moisture (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0
    )


st.subheader("⛰️ Terrain Condition")

slope = st.number_input(
    "Slope Degree",
    min_value=0.0,
    max_value=90.0,
    value=20.0,
    step=1.0
)


st.divider()


summary_1, summary_2, summary_3, summary_4 = st.columns(4)


with summary_1:
    st.metric(
        "📍 Location",
        location
    )


with summary_2:
    st.metric(
        "🌧️ Rainfall",
        f"{rainfall:.0f} mm"
    )


with summary_3:
    st.metric(
        "💧 Soil Moisture",
        f"{soil_moisture:.0f}%"
    )


with summary_4:
    st.metric(
        "⛰️ Slope",
        f"{slope:.0f}°"
    )


st.divider()


predict_button = st.button(
    "🔍 Predict Landslide Risk",
    use_container_width=True
)


if predict_button:

    try:

        new_data = create_input_data(
            location=location,
            rainfall=rainfall,
            soil_moisture=soil_moisture,
            slope=slope,
            elevation=elevation,
            feature_names=model_features
        )


        prediction = model.predict(new_data)

        predicted_class = int(prediction[0])


        probability = None

        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(new_data)

            if probabilities.shape[1] == 2:
                probability = float(probabilities[0][1])
            else:
                probability = float(probabilities[0].max())

        else:

            probability = float(predicted_class)


        risk_level, risk_icon = get_risk_level(
            predicted_class,
            probability
        )


        probability_percent = probability * 100


        st.divider()

        st.header("🚨 Landslide Risk Assessment")


        if risk_level == "CRITICAL":

            st.error(
                f"{risk_icon} LANDSLIDE RISK: {risk_level}"
            )

        elif risk_level == "HIGH":

            st.warning(
                f"{risk_icon} LANDSLIDE RISK: {risk_level}"
            )

        elif risk_level == "MODERATE":

            st.warning(
                f"{risk_icon} LANDSLIDE RISK: {risk_level}"
            )

        else:

            st.success(
                f"{risk_icon} LANDSLIDE RISK: {risk_level}"
            )


        result_left, result_right = st.columns(2)


        with result_left:

            st.metric(
                "🤖 AI Risk Probability",
                f"{probability_percent:.1f}%"
            )


        with result_right:

            st.metric(
                "🎯 Model Classification",
                risk_level
            )


        st.progress(
            min(max(probability, 0.0), 1.0)
        )


        if risk_level == "CRITICAL":

            st.error(
                "The model indicates a very high landslide risk. "
                "Immediate attention to environmental conditions "
                "and official warnings is recommended."
            )

        elif risk_level == "HIGH":

            st.warning(
                "The model indicates elevated landslide risk. "
                "Increased monitoring and caution are recommended."
            )

        elif risk_level == "MODERATE":

            st.warning(
                "The model indicates a moderate level of landslide risk. "
                "Continue monitoring environmental conditions."
            )

        else:

            st.success(
                "Current input conditions indicate a relatively low "
                "landslide risk according to the trained model."
            )


        st.divider()


        st.header("🔎 Environmental Condition Analysis")


        observations = get_environmental_analysis(
            rainfall,
            soil_moisture,
            slope,
            elevation
        )


        for observation in observations:
            st.write(f"• {observation}")


        st.divider()


        st.header("📋 Prediction Input Summary")


        input_summary = pd.DataFrame({
            "Parameter": [
                "Location",
                "Rainfall",
                "Soil Moisture",
