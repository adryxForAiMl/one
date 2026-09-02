import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

data = pd.read_csv("data/sample/landslide_data.csv")

data = pd.get_dummies(data, columns=["location"], dtype=int)

X = data.drop("previous_landslide", axis=1)
y = data["previous_landslide"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
precision = precision_score(y_test, predictions, zero_division=0)
recall = recall_score(y_test, predictions, zero_division=0)
f1 = f1_score(y_test, predictions, zero_division=0)

joblib.dump(
    {
        "model": model,
        "features": X.columns.tolist()
    },
    "models/landslide_model.pkl"
)

print("Model Training Completed")
print("Model Accuracy:", accuracy)
print("Model Precision:", precision)
print("Model Recall:", recall)
print("Model F1 Score:", f1)
print("Model Saved Successfully")

print("\nLandslide Prediction")

location = input("Enter location: ")
rainfall = float(input("Enter rainfall (mm): "))
soil_moisture = float(input("Enter soil moisture (%): "))
slope = float(input("Enter slope degree: "))
elevation = float(input("Enter elevation (m): "))

new_data = pd.DataFrame({
    "location": [location],
    "rainfall_mm": [rainfall],
    "soil_moisture_percent": [soil_moisture],
    "slope_degree": [slope],
    "elevation_m": [elevation]
})

new_data = pd.get_dummies(new_data, columns=["location"])

new_data = new_data.reindex(
    columns=model.feature_names_in_,
    fill_value=0
)

prediction = model.predict(new_data)

if prediction[0] == 1:
    print("\n⚠️ Landslide Risk: HIGH")
else:
    print("\n✅ Landslide Risk: LOW")