import streamlit as st
import pandas as pd
import joblib


st.set_page_config(
    page_title="AI Landslide Early Warning System",
    page_icon="🌧️",
    layout="wide"
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


FEATURE_COLUMNS = [
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


def load_model():
    try:
        model_data = joblib.load(MODEL_PATH)

        if isinstance(model_data, dict):
            if "model" in model_data:
                return model_data["model"]
            else:
                st.error(
                    "The saved model file is a dictionary, "
                    "but the 'model' key was not found."
                )
                st.stop()

        return model_data

    except FileNotFoundError:
        st.error(
            "Model file not found.\n\n"
            "Expected location: models/landslide_model.pkl"
        )
        st.stop()

    except Exception as error:
        st.error(f"Unable to load model: {error}")
        st.stop()


def prepare_input(location, rainfall, soil_moisture, slope, elevation):

    new_data = pd.DataFrame({
        "location": [location],
        "rainfall_mm": [rainfall],
        "soil_moisture_percent": [soil_moisture],
        "slope_degree": [slope],
        "elevation_m": [elevation]
    })

    new_data = pd.get_dummies(
        new_data,
        columns=["location"]
    )

    new_data = new_data.reindex(
        columns=FEATURE_COLUMNS,
        fill_value=0
    )

    return new_data


def calculate_risk_level(prediction, probability):

    if prediction == 1:

        if probability >= 0.80:
            return "CRITICAL"

        if probability >= 0.60:
            return "HIGH"

        return "MODERATE"

    if probability <= 0.20:
        return "LOW"

    return "MODERATE"


def get_risk_message(risk_level):

    messages = {
        "LOW":
            "Current input conditions indicate a relatively low "
            "landslide risk according to the trained model.",

        "MODERATE":
            "The model indicates moderate concern. "
            "Environmental conditions should be monitored.",

        "HIGH":
            "The model indicates a high possibility of landslide. "
            "Extra caution and monitoring are recommended.",

        "CRITICAL":
            "The model indicates a very high landslide risk. "
            "Immediate attention to local environmental conditions "
            "and official warnings is recommended."
    }

    return messages.get(
        risk_level,
        "Risk level could not be determined."
    )


def get_condition_analysis(
    rainfall,
    soil_moisture,
    slope,
    elevation
):

    observations = []

    if rainfall >= 200:
        observations.append(
            "🌧️ High rainfall input"
        )
    elif rainfall >= 100:
        observations.append(
            "🌦️ Moderate rainfall input"
        )
    else:
        observations.append(
            "☀️ Relatively low rainfall input"
        )

    if soil_moisture >= 80:
        observations.append(
            "💧 Very high soil moisture"
        )
    elif soil_moisture >= 60:
        observations.append(
            "💧 Elevated soil moisture"
        )
    else:
        observations.append(
            "🌱 Relatively lower soil moisture"
        )

    if slope >= 40:
        observations.append(
            "⛰️ Steep slope"
        )
    elif slope >= 20:
        observations.append(
            "⛰️ Moderate slope"
        )
    else:
        observations.append(
            "📐 Relatively gentle slope"
        )

    if elevation >= 1500:
        observations.append(
            "🏔️ High elevation"
        )
    elif elevation >= 800:
        observations.append(
            "🏔️ Moderate elevation"
        )
    else:
        observations.append(
            "🌄 Lower elevation"
        )

    return observations


def show_header():

    st.title(
        "🌧️ AI-Based Landslide Early Warning System"
    )

    st.subheader(
        "North Eastern Region (NER)"
    )

    st.write(
        "An interactive machine-learning based system "
        "for estimating landslide risk using environmental "
        "and geographical parameters."
    )

    st.divider()


def show_sidebar():

    with st.sidebar:

        st.header("🛰️ System Information")

        st.write(
            "This application uses a trained machine "
            "learning model to classify landslide risk."
        )

        st.divider()

        st.subheader("Input Parameters")

        st.write("📍 Location")
        st.write("🌧️ Rainfall")
        st.write("💧 Soil Moisture")
        st.write("⛰️ Slope")
        st.write("🏔️ Elevation")

        st.divider()

        st.subheader("Supported Locations")

        for location in LOCATIONS:
            st.write(f"• {location}")

        st.divider()

        st.caption(
            "AI Landslide Early Warning System"
        )


model = load_model()


show_header()
show_sidebar()


st.markdown(
    "## 📊 Environmental Condition Analysis"
)

st.write(
    "Enter the current environmental conditions "
    "to generate a landslide-risk prediction."
)


input_col1, input_col2 = st.columns(2)


with input_col1:

    st.markdown("### 📍 Geographic Information")

    location = st.selectbox(
        "Select Location",
        LOCATIONS
    )

    elevation = st.number_input(
        "Elevation (m)",
        min_value=0.0,
        max_value=10000.0,
        value=1000.0,
        step=50.0
    )


with input_col2:

    st.markdown("### 🌧️ Environmental Conditions")

    rainfall = st.number_input(
        "Rainfall (mm)",
        min_value=0.0,
        max_value=2000.0,
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


st.markdown("### ⛰️ Terrain Condition")

slope = st.number_input(
    "Slope Degree",
    min_value=0.0,
    max_value=90.0,
    value=20.0,
    step=1.0
)


st.divider()


summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)


with summary_col1:

    st.metric(
        "📍 Location",
        location
    )


with summary_col2:

    st.metric(
        "🌧️ Rainfall",
        f"{rainfall:.0f} mm"
    )


with summary_col3:

    st.metric(
        "💧 Soil Moisture",
        f"{soil_moisture:.0f}%"
    )


with summary_col4:

    st.metric(
        "⛰️ Slope",
        f"{slope:.0f}°"
    )


st.divider()


predict_button = st.button(
    "🔍 Predict Landslide Risk",
    type="primary",
    use_container_width=True
)


if predict_button:

    if rainfall < 0:
        st.error(
            "Rainfall cannot be negative."
        )
        st.stop()

    if soil_moisture < 0 or soil_moisture > 100:
        st.error(
            "Soil moisture must be between 0% and 100%."
        )
        st.stop()

    if slope < 0 or slope > 90:
        st.error(
            "Slope degree must be between 0° and 90°."
        )
        st.stop()

    if elevation < 0:
        st.error(
            "Elevation cannot be negative."
        )
        st.stop()


    with st.spinner(
        "Analyzing environmental conditions..."
    ):

        new_data = prepare_input(
            location,
            rainfall,
            soil_moisture,
            slope,
            elevation
        )

        try:

            prediction = model.predict(
                new_data
            )

            prediction_value = int(
                prediction[0]
            )

        except Exception as error:

            st.error(
                f"Prediction failed: {error}"
            )

            st.stop()


        probability = None

        if hasattr(
            model,
            "predict_proba"
        ):

            try:

                probabilities = model.predict_proba(
                    new_data
                )

                probability = float(
                    probabilities[0][1]
                )

            except Exception:
                probability = None


    st.divider()

    st.markdown(
        "## 🚨 Landslide Risk Assessment"
    )


    if probability is not None:

        probability_percent = (
            probability * 100
        )

    else:

        probability_percent = (
            100.0 if prediction_value == 1
            else 0.0
        )


    risk_level = calculate_risk_level(
        prediction_value,
        probability_percent / 100
    )


    result_col1, result_col2 = st.columns(2)


    with result_col1:

        if risk_level == "LOW":

            st.success(
                "🟢 LANDSLIDE RISK: LOW"
            )

        elif risk_level == "MODERATE":

            st.warning(
                "🟡 LANDSLIDE RISK: MODERATE"
            )

        elif risk_level == "HIGH":

            st.error(
                "🟠 LANDSLIDE RISK: HIGH"
            )

        else:

            st.error(
                "🔴 LANDSLIDE RISK: CRITICAL"
            )


    with result_col2:

        st.metric(
            "AI Risk Probability",
            f"{probability_percent:.1f}%"
        )


    st.write(
        get_risk_message(
            risk_level
        )
    )


    if probability is not None:

        st.progress(
            min(
                max(
                    probability,
                    0.0
                ),
                1.0
            )
        )


    st.divider()


    st.markdown(
        "### 🔎 Environmental Condition Analysis"
    )


    conditions = get_condition_analysis(
        rainfall,
        soil_moisture,
        slope,
        elevation
    )


    for condition in conditions:

        st.write(
            f"• {condition}"
        )


    st.divider()


    st.markdown(
        "### 📋 Prediction Input Summary"
    )


    result_data = pd.DataFrame({
        "Parameter": [
            "Location",
            "Rainfall",
            "Soil Moisture",
            "Slope",
            "Elevation",
            "Model Prediction",
            "Risk Level"
        ],

        "Value": [
            location,
            f"{rainfall:.2f} mm",
            f"{soil_moisture:.2f} %",
            f"{slope:.2f}°",
            f"{elevation:.2f} m",
            (
                "Landslide Detected"
                if prediction_value == 1
                else "No Landslide"
            ),
            risk_level
        ]
    })


    st.dataframe(
        result_data,
        use_container_width=True,
        hide_index=True
    )


    st.divider()


    st.markdown(
        "### 🧠 Model Interpretation"
    )


    if prediction_value == 1:

        st.write(
            "The trained machine-learning model classified "
            "the supplied environmental conditions as "
            "corresponding to a landslide-positive class."
        )

    else:

        st.write(
            "The trained machine-learning model classified "
            "the supplied environmental conditions as "
            "corresponding to a landslide-negative class."
        )


    st.info(
        "This prediction is generated by a machine-learning "
        "model and should be treated as a decision-support "
        "result, not as a replacement for official geological "
        "or disaster-management warnings."
    )


st.divider()


st.markdown(
    "## 📚 About the System"
)


about_col1, about_col2 = st.columns(2)


with about_col1:

    st.markdown(
        """
        ### 🎯 Objective

        The objective of this project is to demonstrate
        how machine learning can be applied to landslide
        risk classification.

        The system considers environmental and geographical
        parameters such as:

        - Rainfall
        - Soil moisture
        - Slope degree
        - Elevation
        - Geographic location
        """
    )


with about_col2:

    st.markdown(
        """
        ### ⚙️ Prediction Pipeline

        The application follows the following workflow:

        1. User enters environmental conditions.
        2. Location is converted into machine-readable
           categorical features.
        3. Input columns are aligned with the trained model.
        4. The trained model generates a prediction.
        5. The application calculates the displayed
           risk information.
        6. Results are presented through the dashboard.
        """
    )


st.divider()


st.markdown(
    "### 🛠️ Technology Stack"
)


tech_col1, tech_col2, tech_col3, tech_col4 = st.columns(4)


with tech_col1:
    st.info("🐍 Python")


with tech_col2:
    st.info("📊 Pandas")


with tech_col3:
    st.info("🤖 Scikit-learn")


with tech_col4:
    st.info("🎨 Streamlit")


st.divider()


st.caption(
    "AI-Based Landslide Early Warning System | "
    "North Eastern Region (NER)"
)