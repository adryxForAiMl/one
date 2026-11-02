"""
Geospatial mapping and GIS visualization utilities for Landslide_AI.
Generates interactive Folium maps with geological risk zones, monitoring stations,
and live telemetry indicators for the North Eastern Region & Himalayas.
"""

from typing import List, Dict, Any, Optional
import folium
from folium import plugins

from src.config import LOCATION_COORDINATES, RISK_LEVELS


def create_landslide_map(
    stations: Optional[List[Dict[str, Any]]] = None,
    center_lat: float = 26.15,
    center_lon: float = 92.8,
    zoom_start: int = 7,
    tile_layer: str = "CartoDB positron"
) -> folium.Map:
    """
    Creates an interactive GIS folium map visualizing landslide monitoring stations,
    regional risk levels, and hazard heatmaps.
    """
    # Create base folium map
    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles=tile_layer,
        control_scale=True,
    )

    # Add satellite imagery option
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Hybrid Satellite",
        name="Satellite Imagery",
        overlay=False,
        control=True
    ).add_to(fmap)

    # Default stations from LOCATION_COORDINATES if none provided
    if stations is None:
        stations = []
        for loc, data in LOCATION_COORDINATES.items():
            stations.append({
                "location": loc,
                "lat": data["lat"],
                "lon": data["lon"],
                "elevation_m": data["elevation"],
                "district": data["district"],
                "risk_level": "MODERATE" if "Sikkim" in loc or "Meghalaya" in loc else "LOW",
                "probability_percent": 48.0 if "Sikkim" in loc else 18.0,
                "rainfall_mm": 135.0 if "Sikkim" in loc else 35.0,
                "soil_moisture_percent": 72.0 if "Sikkim" in loc else 42.0,
                "slope_degree": 38.0 if "Sikkim" in loc else 18.0,
            })

    # Prepare marker cluster for clean browsing
    marker_cluster = plugins.MarkerCluster(name="Monitoring Stations").add_to(fmap)

    heat_data = []

    for st in stations:
        lat = st.get("lat")
        lon = st.get("lon")
        if lat is None or lon is None:
            continue

        risk = st.get("risk_level", "LOW")
        prob = st.get("probability_percent", 0.0)
        rainfall = st.get("rainfall_mm", 0.0)
        moisture = st.get("soil_moisture_percent", 0.0)
        slope = st.get("slope_degree", 0.0)
        elev = st.get("elevation_m", 0.0)
        loc_name = st.get("location", "Monitoring Station")
        district = st.get("district", "Regional Sector")

        # Color mapping
        if risk == "CRITICAL":
            marker_color = "red"
            badge_bg = "#f44336"
            heat_weight = 1.0
        elif risk == "HIGH":
            marker_color = "orange"
            badge_bg = "#ff9800"
            heat_weight = 0.75
        elif risk == "MODERATE":
            marker_color = "beige"
            badge_bg = "#ffeb3b"
            heat_weight = 0.45
        else:
            marker_color = "green"
            badge_bg = "#00e676"
            heat_weight = 0.2

        heat_data.append([lat, lon, heat_weight])

        popup_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    width: 250px; padding: 6px; color: #1e293b;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0; font-size: 15px; color: #0f172a; font-weight: 700;">{loc_name}</h4>
                <span style="background: {badge_bg}; color: {'#000' if risk=='MODERATE' else '#fff'};
                             padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700;">
                    {risk}
                </span>
            </div>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 8px;">📍 {district}</div>
            
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <tr><td style="color:#64748b; padding:2px 0;">Risk Probability:</td><td style="font-weight:700; text-align:right;">{prob:.1f}%</td></tr>
                <tr><td style="color:#64748b; padding:2px 0;">24h Rainfall:</td><td style="font-weight:700; text-align:right;">{rainfall:.1f} mm</td></tr>
                <tr><td style="color:#64748b; padding:2px 0;">Soil Moisture:</td><td style="font-weight:700; text-align:right;">{moisture:.1f}%</td></tr>
                <tr><td style="color:#64748b; padding:2px 0;">Slope Angle:</td><td style="font-weight:700; text-align:right;">{slope:.1f}°</td></tr>
                <tr><td style="color:#64748b; padding:2px 0;">Elevation:</td><td style="font-weight:700; text-align:right;">{elev:.0f} m</td></tr>
            </table>
            
            <div style="margin-top: 8px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #334155;">
                <strong>Action:</strong> {RISK_LEVELS.get(risk, {}).get('action', 'Monitoring')}
            </div>
        </div>
        """

        # Add Marker
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loc_name} — Landslide Risk: {risk} ({prob:.1f}%)",
            icon=folium.Icon(color=marker_color, icon="tint" if rainfall > 50 else "mountain", prefix="fa")
        ).add_to(marker_cluster)

        # Pulse circle for high or critical risk
        if risk in ["HIGH", "CRITICAL"]:
            folium.Circle(
                location=[lat, lon],
                radius=15000 if risk == "CRITICAL" else 8000,
                color="#f44336" if risk == "CRITICAL" else "#ff9800",
                fill=True,
                fill_color="#f44336" if risk == "CRITICAL" else "#ff9800",
                fill_opacity=0.25,
                weight=2,
                tooltip=f"Hazard Warning Zone ({loc_name})"
            ).add_to(fmap)

    # Add heatmap layer
    if heat_data:
        plugins.HeatMap(
            heat_data,
            name="Susceptibility Heatmap",
            radius=25,
            blur=18,
            min_opacity=0.35,
            gradient={0.2: "#00e676", 0.5: "#ffeb3b", 0.75: "#ff9800", 1.0: "#f44336"}
        ).add_to(fmap)

    # Add layer control
    folium.LayerControl().add_to(fmap)
    return fmap
