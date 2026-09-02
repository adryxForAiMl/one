# AI Landslide Early Warning System

## Project Overview

The AI Landslide Early Warning System is a machine learning based application designed to assess landslide risk using environmental and geographical conditions.

The system uses a Random Forest Classifier to analyze factors such as rainfall, soil moisture, slope, elevation, and location.

The project provides an interactive Streamlit dashboard where users can enter environmental conditions and receive a landslide risk assessment.

## Objectives

- Predict landslide risk using machine learning.
- Analyze important environmental conditions.
- Provide an interactive and easy-to-use dashboard.
- Display risk probability and risk level.
- Provide recommendations based on environmental conditions.
- Demonstrate an end-to-end AI/ML workflow.

## Input Features

The model uses the following input parameters:

- Location
- Rainfall (mm)
- Soil Moisture (%)
- Slope (degrees)
- Elevation (m)

## Target Variable

The target variable used for model training is:

`previous_landslide`

Where:

- `1` = Landslide class
- `0` = Non-landslide class

## Machine Learning Model

The project uses:

**Random Forest Classifier**

Training configuration:

- Number of estimators: 100
- Random state: 42
- Test size: 20%

## Model Performance

Current performance on the available sample test split:

| Metric | Score |
|---|---:|
| Accuracy | 100% |
| Precision | 100% |
| Recall | 100% |
| F1 Score | 100% |

### Important Note

The current dataset contains only a small number of sample records. Therefore, these scores represent performance on the current sample/test split and should not be interpreted as 100% real-world prediction accuracy.

A real-world landslide warning system would require a much larger and validated dataset.

## Application Features

- Interactive Streamlit interface
- Environmental condition inputs
- Location selection
- Landslide risk prediction
- Risk probability visualization
- Risk classification
- Prediction history
- Environmental condition analysis
- Safety recommendations
- CSV export
- Model information
- Performance metrics

## Technology Stack

- Python
- Pandas
- Scikit-learn
- Random Forest
- Joblib
- Streamlit
- HTML
- CSS

## Project Structure

```text
Landslide_AI/
│
├── app.py
├── main.py
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
│       └── landslide_data.csv
│
├── models/
│   └── landslide_model.pkl
│
└── landslide_env/