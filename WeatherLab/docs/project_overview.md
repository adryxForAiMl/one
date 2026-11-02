# WeatherLab project overview

WeatherLab is a Python desktop application for exploring interpolation,
equation solving, numerical calculus, differential equations, and data fitting.
The CustomTkinter interface provides a dedicated workspace and visualization
for each supported method.

Numerical algorithms belong in `backend/`, UI code in `frontend/`, and reusable
plotting helpers in `visualization/`. The navigation registry connects each
workspace to its corresponding method page. Run the app from this folder with
`python3 app.py` after installing `requirements.txt`.
