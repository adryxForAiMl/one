import streamlit as st
import pandas as pd
import joblib
import html


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Landslide Early Warning System",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "models/landslide_model.pkl"

LOCATIONS = [
    "Sikkim",
    "Arunachal Pradesh",
    "Assam",
    "Meghalaya",
    "Nagaland",
    "Mizoram",
    "Tripura",
]

DEFAULT_FEATURE_COLUMNS = [
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
    "location_Tripura",
]


# ============================================================
# SESSION STATE
# ============================================================

if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []


# ============================================================
# HTML RENDER HELPER
# ============================================================

def render_html(content):
    """
    Render HTML correctly.

    Newer Streamlit versions use st.html().
    Older versions fall back to st.markdown().
    """

    if hasattr(st, "html"):
        st.html(content)
    else:
        st.markdown(
            content,
            unsafe_allow_html=True,
        )


# ============================================================
# CUSTOM CSS
# ============================================================

CUSTOM_CSS = """
<style>

html, body {
    background: #07111f;
}

/* ==========================================================
   MAIN APPLICATION
   ========================================================== */

.stApp {
    background:
        radial-gradient(
            circle at 85% 5%,
            rgba(0, 180, 255, 0.13),
            transparent 30%
        ),
        radial-gradient(
            circle at 10% 80%,
            rgba(30, 80, 180, 0.08),
            transparent 30%
        ),
        linear-gradient(
            135deg,
            #07111f 0%,
            #0b1626 50%,
            #07111f 100%
        );
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #091625 0%,
            #07111f 100%
        );

    border-right: 1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] * {
    color: #e8f0f7;
}


/* ==========================================================
   HERO
   ========================================================== */

.hero {
    padding: 34px;
    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            rgba(20, 35, 55, 0.98),
            rgba(9, 24, 40, 0.98)
        );

    border: 1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 18px 50px rgba(0,0,0,0.30);

    margin-bottom: 30px;
}

.hero-title {
    color: #ffffff;

    font-size: 42px;
    font-weight: 800;

    line-height: 1.15;

    margin-bottom: 10px;

    letter-spacing: -1px;
}

.hero-subtitle {
    color: #67dfff;

    font-size: 20px;
    font-weight: 700;

    margin-bottom: 15px;
}

.hero-description {
    color: #d5e2ef;

    font-size: 17px;

    line-height: 1.6;

    max-width: 850px;
}

.hero-badges {
    margin-top: 18px;
}

.hero-badge {
    display: inline-block;

    padding: 8px 14px;

    margin-right: 8px;
    margin-bottom: 8px;

    border-radius: 999px;

    background:
        rgba(0,200,255,0.12);

    border:
        1px solid rgba(0,200,255,0.25);

    color: #67dfff;

    font-size: 13px;
    font-weight: 700;
}


/* ==========================================================
   SECTION TITLES
   ========================================================== */

.section-title {
    color: #ffffff;

    font-size: 28px;
    font-weight: 800;

    margin-top: 20px;
    margin-bottom: 6px;
}

.section-subtitle {
    color: #94a6b9;

    font-size: 15px;

    margin-bottom: 20px;
}


/* ==========================================================
   INFO CARDS
   ========================================================== */

.info-card {
    padding: 20px;

    border-radius: 18px;

    background:
        linear-gradient(
            145deg,
            rgba(22,42,64,0.95),
            rgba(14,30,48,0.95)
        );

    border:
        1px solid rgba(255,255,255,0.08);

    min-height: 110px;

    box-shadow:
        0 10px 30px rgba(0,0,0,0.18);
}

.info-label {
    color: #91a5ba;

    font-size: 12px;
    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: 0.8px;

    margin-bottom: 8px;
}

.info-value {
    color: #ffffff;

    font-size: 24px;
    font-weight: 800;
}


/* ==========================================================
   RISK CARDS
   ========================================================== */

.risk-card {
    padding: 28px;

    border-radius: 22px;

    margin-top: 10px;
    margin-bottom: 20px;

    min-height: 170px;

    border:
        1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 16px 45px rgba(0,0,0,0.28);
}

.risk-low {
    background:
        linear-gradient(
            135deg,
            rgba(17,105,66,0.95),
            rgba(9,65,45,0.95)
        );
}

.risk-moderate {
    background:
        linear-gradient(
            135deg,
            rgba(137,107,12,0.95),
            rgba(90,69,8,0.95)
        );
}

.risk-high {
    background:
        linear-gradient(
            135deg,
            rgba(142,67,22,0.95),
            rgba(91,42,15,0.95)
        );
}

.risk-critical {
    background:
        linear-gradient(
            135deg,
            rgba(145,30,39,0.97),
            rgba(82,17,25,0.97)
        );
}

.risk-title {
    color: #ffffff;

    font-size: 30px;
    font-weight: 800;

    margin-bottom: 10px;
}

.risk-description {
    color: #e8f0f7;

    font-size: 16px;

    line-height: 1.6;
}


/* ==========================================================
   GAUGE
   ========================================================== */

.gauge-wrapper {
    display: flex;

    justify-content: center;
    align-items: center;

    padding: 10px;
}

.gauge {
    width: 210px;
    height: 210px;

    border-radius: 50%;

    display: flex;

    align-items: center;
    justify-content: center;

    background:
        conic-gradient(
            #00d084 var(--risk),
            rgba(255,255,255,0.10) var(--risk)
        );

    position: relative;

    box-shadow:
        0 10px 35px rgba(0,0,0,0.25);
}

.gauge::before {
    content: "";

    position: absolute;

    width: 155px;
    height: 155px;

    border-radius: 50%;

    background: #0b1626;
}

.gauge-content {
    position: relative;

    z-index: 2;

    text-align: center;
}

.gauge-number {
    color: #ffffff;

    font-size: 34px;
    font-weight: 800;
}

.gauge-label {
    color: #9db0c4;

    font-size: 12px;

    text-transform: uppercase;

    max-width: 100px;
}


/* ==========================================================
   CONDITION CARDS
   ========================================================== */

.condition-card {
    padding: 17px 18px;

    border-radius: 15px;

    background:
        rgba(20,34,52,0.88);

    border:
        1px solid rgba(255,255,255,0.07);

    min-height: 65px;

    display: flex;

    align-items: center;

    color: #e5edf5;

    font-size: 14px;

    line-height: 1.4;
}


/* ==========================================================
   RECOMMENDATION
   ========================================================== */

.recommendation {
    padding: 20px;

    border-radius: 17px;

    background:
        rgba(20,34,52,0.90);

    border-left:
        5px solid #00b7ff;

    color: #dce8f3;

    line-height: 1.6;

    margin-top: 18px;
}


/* ==========================================================
   ABOUT CARDS
   ========================================================== */

.about-card {
    background:
        rgba(20,34,52,0.78);

    border:
        1px solid rgba(255,255,255,0.07);

    border-radius: 16px;

    padding: 22px;

    min-height: 190px;
}

.about-card h3 {
    color: #ffffff;

    margin-top: 0;

    margin-bottom: 12px;
}

.about-card p,
.about-card li {
    color: #c9d7e5;

    line-height: 1.6;
}


/* ==========================================================
   TECHNOLOGY CARDS
   ========================================================== */

.tech-card {
    background:
        linear-gradient(
            135deg,
            #183a60,
            #122d4b
        );

    border:
        1px solid rgba(255,255,255,0.07);

    border-radius: 14px;

    padding: 15px;

    text-align: center;

    color: #dcecff;

    font-weight: 700;
}


/* ==========================================================
   FOOTER
   ========================================================== */

.footer {
    text-align: center;

    color: #71849a;

    font-size: 13px;

    padding: 28px 0 5px;
}


/* ==========================================================
   STREAMLIT ELEMENTS
   ========================================================== */

[data-testid="stMetric"] {
    background:
        rgba(20,34,52,0.78);

    padding: 15px;

    border-radius: 16px;

    border:
        1px solid rgba(255,255,255,0.07);
}

div.stButton > button {
    border-radius: 14px;

    font-weight: 750;

    min-height: 52px;
}

hr {
    border-color: rgba(255,255,255,0.10);
}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media (max-width: 800px) {

    .hero-title {
        font-size: 30px;
    }

    .hero-subtitle {
        font-size: 17px;
    }

    .hero-description {
        font-size: 15px;
    }

    .section-title {
        font-size: 24px;
    }
}

</style>
"""


# Render CSS
render_html(CUSTOM_CSS)


# ============================================================
# MODEL LOADING
# ============================================================

@st.cache_resource
def load_model():

    try:

        model_data = joblib.load(MODEL_PATH)

        if isinstance(model_data, dict):

            if "model" not in model_data:

                st.error(
                    "The model file is a dictionary, "
                    "but the 'model' key was not found."
                )

                st.stop()

            model = model_data["model"]
            metadata = model_data

        else:

            model = model_data
            metadata = {}

        return model, metadata

    except FileNotFoundError:

        st.error(
            "❌ Model file not found.\n\n"
            "Expected file:\n"
            f"`{MODEL_PATH}`"
        )

        st.stop()

    except Exception as error:

        st.error(
            "❌ Unable to load the trained model."
        )

        st.exception(error)

        st.stop()


# ============================================================
# FEATURE COLUMNS
# ============================================================

def get_feature_columns(model, metadata):

    if "feature_columns" in metadata:

        return list(
            metadata["feature_columns"]
        )

    if "features" in metadata:

        return list(
            metadata["features"]
        )

    if hasattr(model, "feature_names_in_"):

        return list(
            model.feature_names_in_
        )

    return DEFAULT_FEATURE_COLUMNS


# ============================================================
# PREPARE MODEL INPUT
# ============================================================

def prepare_input(
    location,
    rainfall,
    soil_moisture,
    slope,
    elevation,
    model,
    metadata,
):

    raw_data = pd.DataFrame(
        {
            "location": [location],
            "rainfall_mm": [rainfall],
            "soil_moisture_percent": [soil_moisture],
            "slope_degree": [slope],
            "elevation_m": [elevation],
        }
    )

    # --------------------------------------------------------
    # If model is a complete sklearn Pipeline,
    # pass the raw dataframe.
    # --------------------------------------------------------

    if hasattr(model, "named_steps"):

        return raw_data

    # --------------------------------------------------------
    # Manual one-hot encoding
    # --------------------------------------------------------

    encoded_data = pd.get_dummies(
        raw_data,
        columns=["location"],
    )

    feature_columns = get_feature_columns(
        model,
        metadata,
    )

    encoded_data = encoded_data.reindex(
        columns=feature_columns,
        fill_value=0,
    )

    return encoded_data


# ============================================================
# PROBABILITY
# ============================================================

def get_probability(
    model,
    input_data,
    prediction_value,
):

    if not hasattr(model, "predict_proba"):

        return (
            100.0
            if prediction_value == 1
            else 0.0
        )

    try:

        probabilities = model.predict_proba(
            input_data
        )

        if hasattr(model, "classes_"):

            classes = list(
                model.classes_
            )

            if 1 in classes:

                class_index = classes.index(1)

                return float(
                    probabilities[0][class_index]
                    * 100
                )

        if len(probabilities[0]) >= 2:

            return float(
                probabilities[0][1] * 100
            )

    except Exception:

        pass

    return (
        100.0
        if prediction_value == 1
        else 0.0
    )


# ============================================================
# RISK LEVEL
# ============================================================

def calculate_risk_level(
    probability_percent,
):

    if probability_percent >= 75:

        return "CRITICAL"

    if probability_percent >= 50:

        return "HIGH"

    if probability_percent >= 25:

        return "MODERATE"

    return "LOW"


# ============================================================
# RISK CSS CLASS
# ============================================================

def risk_class(risk_level):

    return {
        "LOW": "risk-low",
        "MODERATE": "risk-moderate",
        "HIGH": "risk-high",
        "CRITICAL": "risk-critical",
    }.get(
        risk_level,
        "risk-moderate",
    )


# ============================================================
# RISK EMOJI
# ============================================================

def risk_emoji(risk_level):

    return {
        "LOW": "🟢",
        "MODERATE": "🟡",
        "HIGH": "🟠",
        "CRITICAL": "🔴",
    }.get(
        risk_level,
        "⚪",
    )


# ============================================================
# RISK MESSAGE
# ============================================================

def risk_message(risk_level):

    messages = {

        "LOW":
            "Current environmental inputs indicate "
            "relatively low landslide risk according "
            "to the trained model.",

        "MODERATE":
            "The model indicates moderate concern. "
            "Environmental conditions should be "
            "monitored carefully.",

        "HIGH":
            "The model indicates elevated landslide "
            "risk. Increased caution and environmental "
            "monitoring are recommended.",

        "CRITICAL":
            "The model indicates very high landslide "
            "risk. Pay close attention to local "
            "conditions and official warnings.",
    }

    return messages.get(
        risk_level,
        "Risk level could not be determined.",
    )


# ============================================================
# RECOMMENDATION
# ============================================================

def get_recommendation(risk_level):

    recommendations = {

        "LOW":
            "Continue routine monitoring of rainfall, "
            "soil moisture and terrain conditions.",

        "MODERATE":
            "Monitor rainfall and soil moisture closely. "
            "Reassess the location if environmental "
            "conditions worsen.",

        "HIGH":
            "Increase monitoring frequency and exercise "
            "additional caution around steep or unstable "
            "terrain. Follow official advisories.",

        "CRITICAL":
            "Treat this as a high-priority warning signal. "
            "Check official disaster-management and local "
            "authority warnings and follow their instructions.",
    }

    return recommendations.get(
        risk_level,
        "Continue monitoring environmental conditions.",
    )


# ============================================================
# ENVIRONMENTAL CONDITION ANALYSIS
# ============================================================

def condition_analysis(
    rainfall,
    soil_moisture,
    slope,
    elevation,
):

    conditions = []

    if rainfall >= 200:

        conditions.append(
            "🌧️ High rainfall input"
        )

    elif rainfall >= 100:

        conditions.append(
            "🌦️ Moderate rainfall input"
        )

    else:

        conditions.append(
            "☀️ Relatively low rainfall input"
        )

    if soil_moisture >= 80:

        conditions.append(
            "💧 Very high soil moisture"
        )

    elif soil_moisture >= 60:

        conditions.append(
            "💧 Elevated soil moisture"
        )

    elif soil_moisture >= 30:

        conditions.append(
            "🌱 Moderate soil moisture"
        )

    else:

        conditions.append(
            "🌱 Relatively low soil moisture"
        )

    if slope >= 40:

        conditions.append(
            "⛰️ Steep slope"
        )

    elif slope >= 20:

        conditions.append(
            "⛰️ Moderate slope"
        )

    else:

        conditions.append(
            "📐 Relatively gentle slope"
        )

    if elevation >= 1500:

        conditions.append(
            "🏔️ High elevation"
        )

    elif elevation >= 800:

        conditions.append(
            "🏔️ Moderate elevation"
        )

    else:

        conditions.append(
            "🌄 Lower elevation"
        )

    return conditions


# ============================================================
# INFO CARD
# ============================================================

def render_info_card(
    label,
    value,
):

    safe_label = html.escape(
        str(label)
    )

    safe_value = html.escape(
        str(value)
    )

    render_html(
        f"""
        <div class="info-card">

            <div class="info-label">
                {safe_label}
            </div>

            <div class="info-value">
                {safe_value}
            </div>

        </div>
        """
    )


# ============================================================
# LOAD MODEL
# ============================================================

model, metadata = load_model()


# ============================================================
# AVAILABLE LOCATIONS
# ============================================================

available_locations = metadata.get(
    "locations",
    LOCATIONS,
)

if not available_locations:

    available_locations = LOCATIONS


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## 🛰️ System Control"
    )

    st.write(
        "AI-based landslide-risk classification "
        "for the North Eastern Region of India."
    )

    st.divider()

    st.markdown(
        "### 📍 Supported Locations"
    )

    for location_item in available_locations:

        st.write(
            f"• {location_item}"
        )

    st.divider()

    st.markdown(
        "### 🤖 Model"
    )

    model_name = metadata.get(
        "model_name",
        type(model).__name__,
    )

    st.write(
        model_name
    )

    if "metrics" in metadata:

        st.divider()

        st.markdown(
            "### 📊 Model Performance"
        )

        metrics = metadata["metrics"]

        if isinstance(metrics, dict):

            for name, value in metrics.items():

                st.write(
                    f"**{name}:** {value}"
                )

    st.divider()

    st.caption(
        "Decision-support system. "
        "Not a replacement for official warnings."
    )


# ============================================================
# HERO
# ============================================================

render_html(
    """
    <div class="hero">

        <div class="hero-title">
            🌧️ AI-Based Landslide Early Warning System
        </div>

        <div class="hero-subtitle">
            North Eastern Region (NER)
        </div>

        <div class="hero-description">
            An interactive machine-learning system for
            estimating landslide risk from environmental
            and geographical parameters.
        </div>

        <div class="hero-badges">

            <span class="hero-badge">
                🤖 MACHINE LEARNING ENABLED
            </span>

            <span class="hero-badge">
                📍 7 NER LOCATIONS
            </span>

            <span class="hero-badge">
                ⚡ AI PREDICTION
            </span>

        </div>

    </div>
    """
)


# ============================================================
# INPUT SECTION
# ============================================================

render_html(
    """
    <div class="section-title">
        📊 Environmental Monitoring
    </div>

    <div class="section-subtitle">
        Enter environmental conditions and generate
        an AI-based risk assessment.
    </div>
    """
)


input_col1, input_col2 = st.columns(2)


# ============================================================
# GEOGRAPHIC INFORMATION
# ============================================================

with input_col1:

    st.markdown(
        "### 📍 Geographic Information"
    )

    location = st.selectbox(
        "Select Location",
        available_locations,
    )

    elevation = st.number_input(
        "Elevation (m)",
        min_value=0.0,
        max_value=10000.0,
        value=1000.0,
        step=50.0,
    )


# ============================================================
# ENVIRONMENTAL CONDITIONS
# ============================================================

with input_col2:

    st.markdown(
        "### 🌧️ Environmental Conditions"
    )

    rainfall = st.number_input(
        "Rainfall (mm)",
        min_value=0.0,
        max_value=2000.0,
        value=100.0,
        step=10.0,
    )

    soil_moisture = st.number_input(
        "Soil Moisture (%)",
        min_value=0.0,
        max_value=100.0,
        value=50.0,
        step=1.0,
    )


# ============================================================
# TERRAIN
# ============================================================

st.markdown(
    "### ⛰️ Terrain Condition"
)

slope = st.number_input(
    "Slope Degree",
    min_value=0.0,
    max_value=90.0,
    value=20.0,
    step=1.0,
)


# ============================================================
# CURRENT INPUT SUMMARY
# ============================================================

st.divider()

metric_col1, metric_col2, metric_col3, metric_col4 = (
    st.columns(4)
)


with metric_col1:

    render_info_card(
        "📍 Location",
        location,
    )


with metric_col2:

    render_info_card(
        "🌧️ Rainfall",
        f"{rainfall:.0f} mm",
    )


with metric_col3:

    render_info_card(
        "💧 Soil Moisture",
        f"{soil_moisture:.0f}%",
    )


with metric_col4:

    render_info_card(
        "⛰️ Slope",
        f"{slope:.0f}°",
    )


st.markdown("")


# ============================================================
# PREDICTION BUTTON
# ============================================================

predict_button = st.button(
    "🔍  PREDICT LANDSLIDE RISK",
    type="primary",
    use_container_width=True,
)


# ============================================================
# PREDICTION
# ============================================================

if predict_button:

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if rainfall < 0:

        st.error(
            "Rainfall cannot be negative."
        )

        st.stop()

    if not 0 <= soil_moisture <= 100:

        st.error(
            "Soil moisture must be between 0% and 100%."
        )

        st.stop()

    if not 0 <= slope <= 90:

        st.error(
            "Slope must be between 0° and 90°."
        )

        st.stop()

    if elevation < 0:

        st.error(
            "Elevation cannot be negative."
        )

        st.stop()

    # --------------------------------------------------------
    # Run model
    # --------------------------------------------------------

    with st.spinner(
        "🔄 Analyzing environmental conditions..."
    ):

        try:

            input_data = prepare_input(
                location=location,
                rainfall=rainfall,
                soil_moisture=soil_moisture,
                slope=slope,
                elevation=elevation,
                model=model,
                metadata=metadata,
            )

            prediction = model.predict(
                input_data
            )

            prediction_value = int(
                prediction[0]
            )

            probability_percent = get_probability(
                model=model,
                input_data=input_data,
                prediction_value=prediction_value,
            )

        except Exception as error:

            st.error(
                "❌ Prediction failed."
            )

            st.exception(error)

            st.stop()

    # --------------------------------------------------------
    # Limit probability
    # --------------------------------------------------------

    probability_percent = min(
        max(
            float(probability_percent),
            0.0,
        ),
        100.0,
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    risk_level = calculate_risk_level(
        probability_percent
    )

    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    history_item = {

        "Location": location,

        "Rainfall (mm)": round(
            rainfall,
            2,
        ),

        "Soil Moisture (%)": round(
            soil_moisture,
            2,
        ),

        "Slope (°)": round(
            slope,
            2,
        ),

        "Elevation (m)": round(
            elevation,
            2,
        ),

        "Risk Probability (%)": round(
            probability_percent,
            1,
        ),

        "Risk Level": risk_level,
    }

    st.session_state.prediction_history.append(
        history_item
    )

    # ========================================================
    # RESULT
    # ========================================================

    st.divider()

    render_html(
        """
        <div class="section-title">
            🚨 Landslide Risk Assessment
        </div>
        """
    )

    left_result, right_result = st.columns(
        [2, 1]
    )


    # --------------------------------------------------------
    # Risk result
    # --------------------------------------------------------

    with left_result:

        safe_level = html.escape(
            risk_level
        )

        safe_message = html.escape(
            risk_message(risk_level)
        )

        render_html(
            f"""
            <div class="risk-card {risk_class(risk_level)}">

                <div class="risk-title">
                    {risk_emoji(risk_level)}
                    LANDSLIDE RISK: {safe_level}
                </div>

                <div class="risk-description">
                    {safe_message}
                </div>

            </div>
            """
        )


    # --------------------------------------------------------
    # Gauge
    # --------------------------------------------------------

    with right_result:

        render_html(
            f"""
            <div class="gauge-wrapper">

                <div
                    class="gauge"
                    style="--risk:{probability_percent}%"
                >

                    <div class="gauge-content">

                        <div class="gauge-number">
                            {probability_percent:.1f}%
                        </div>

                        <div class="gauge-label">
                            AI Risk Probability
                        </div>

                    </div>

                </div>

            </div>
            """
        )


    # --------------------------------------------------------
    # Progress bar
    # --------------------------------------------------------

    st.progress(
        probability_percent / 100
    )


    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    safe_recommendation = html.escape(
        get_recommendation(
            risk_level
        )
    )

    render_html(
        f"""
        <div class="recommendation">

            <strong>
                ⚠️ Recommended Action
            </strong>

            <br><br>

            {safe_recommendation}

        </div>
        """
    )


    # ========================================================
    # CONDITION ANALYSIS
    # ========================================================

    st.divider()

    st.markdown(
        "### 🔎 Environmental Condition Analysis"
    )

    conditions = condition_analysis(
        rainfall=rainfall,
        soil_moisture=soil_moisture,
        slope=slope,
        elevation=elevation,
    )

    condition_columns = st.columns(4)

    for index, condition in enumerate(
        conditions
    ):

        with condition_columns[index]:

            safe_condition = html.escape(
                condition
            )

            render_html(
                f"""
                <div class="condition-card">
                    {safe_condition}
                </div>
                """
            )


    # ========================================================
    # PREDICTION SUMMARY
    # ========================================================

    st.divider()

    st.markdown(
        "### 📋 Prediction Input Summary"
    )

    prediction_text = (
        "Landslide Detected"
        if prediction_value == 1
        else "No Landslide"
    )

    result_data = pd.DataFrame(
        {
            "Parameter": [

                "Location",

                "Rainfall",

                "Soil Moisture",

                "Slope",

                "Elevation",

                "Model Prediction",

                "AI Risk Probability",

                "Risk Level",

            ],

            "Value": [

                location,

                f"{rainfall:.2f} mm",

                f"{soil_moisture:.2f}%",

                f"{slope:.2f}°",

                f"{elevation:.2f} m",

                prediction_text,

                f"{probability_percent:.1f}%",

                risk_level,

            ],
        }
    )

    st.dataframe(
        result_data,
        use_container_width=True,
        hide_index=True,
    )


    # --------------------------------------------------------
    # CSV DOWNLOAD
    # --------------------------------------------------------

    report_csv = result_data.to_csv(
        index=False
    )

    st.download_button(
        "⬇️ Download Prediction Report",
        data=report_csv,
        file_name="landslide_prediction_report.csv",
        mime="text/csv",
        use_container_width=True,
    )


    # ========================================================
    # MODEL INTERPRETATION
    # ========================================================

    st.divider()

    st.markdown(
        "### 🧠 Model Interpretation"
    )

    if prediction_value == 1:

        st.error(
            "The trained machine-learning model classified "
            "the supplied environmental conditions as "
            "LANDSLIDE POSITIVE."
        )

    else:

        st.success(
            "The trained machine-learning model classified "
            "the supplied environmental conditions as "
            "LANDSLIDE NEGATIVE."
        )


    interpretation_col1, interpretation_col2 = (
        st.columns(2)
    )


    with interpretation_col1:

        st.metric(
            "🌧️ Rainfall",
            f"{rainfall:.1f} mm",
        )

        st.metric(
            "💧 Soil Moisture",
            f"{soil_moisture:.1f}%",
        )


    with interpretation_col2:

        st.metric(
            "⛰️ Slope",
            f"{slope:.1f}°",
        )

        st.metric(
            "🏔️ Elevation",
            f"{elevation:.0f} m",
        )


    st.info(
        "The displayed probability is generated from the "
        "trained machine-learning classifier. This system "
        "is intended for decision-support and demonstration "
        "purposes and should not replace official geological, "
        "meteorological, or disaster-management warnings."
    )


# ============================================================
# PREDICTION HISTORY
# ============================================================

st.divider()

st.markdown(
    "## 📈 Prediction History"
)

if len(
    st.session_state.prediction_history
) == 0:

    st.info(
        "No predictions have been recorded "
        "during this session yet."
    )

else:

    history_df = pd.DataFrame(
        st.session_state.prediction_history
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ABOUT THE SYSTEM
# ============================================================

st.divider()

st.markdown(
    "## 📚 About the System"
)

about_col1, about_col2, about_col3 = (
    st.columns(3)
)


with about_col1:

    render_html(
        """
        <div class="about-card">

            <h3>
                🎯 Objective
            </h3>

            <p>
                Demonstrate how machine learning can
                classify landslide risk using environmental
                and geographical parameters.
            </p>

        </div>
        """
    )


with about_col2:

    render_html(
        """
        <div class="about-card">

            <h3>
                📥 Input Parameters
            </h3>

            <ul>
                <li>Location</li>
                <li>Rainfall</li>
                <li>Soil Moisture</li>
                <li>Slope</li>
                <li>Elevation</li>
            </ul>

        </div>
        """
    )


with about_col3:

    render_html(
        """
        <div class="about-card">

            <h3>
                ⚙️ Prediction Pipeline
            </h3>

            <p>
                Input → Feature Encoding → ML Model
                → Probability → Risk Classification
                → Dashboard Result
            </p>

        </div>
        """
    )


# ============================================================
# TECHNOLOGY STACK
# ============================================================

st.divider()

st.markdown(
    "### 🛠️ Technology Stack"
)

tech_col1, tech_col2, tech_col3, tech_col4 = (
    st.columns(4)
)


with tech_col1:

    render_html(
        """
        <div class="tech-card">
            🐍 Python
        </div>
        """
    )


with tech_col2:

    render_html(
        """
        <div class="tech-card">
            📊 Pandas
        </div>
        """
    )


with tech_col3:

    render_html(
        """
        <div class="tech-card">
            🤖 Scikit-learn
        </div>
        """
    )


with tech_col4:

    render_html(
        """
        <div class="tech-card">
            🎨 Streamlit
        </div>
        """
    )


# ============================================================
# FOOTER
# ============================================================

render_html(
    """
    <div class="footer">

        AI-Based Landslide Early Warning System
        &nbsp;|&nbsp;
        North Eastern Region (NER)
        &nbsp;|&nbsp;
        Machine Learning Decision Support

    </div>
    """
)
