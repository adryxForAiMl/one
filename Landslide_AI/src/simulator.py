"""
IoT Sensor Telemetry Simulator for Landslide_AI.
Simulates real-time telemetry streaming from geotechnical wireless sensor networks
deployed along active mountain slopes and road corridors.
"""

import time
import random
import datetime
from typing import Dict, Any, List


class SensorStationSimulator:
    """
    Simulates real-time geotechnical sensor data streams.
    """

    STATIONS = [
        {"id": "ST-01", "name": "Gangtok Highway Ridge", "state": "Sikkim", "lat": 27.3389, "lon": 88.6065, "elevation": 1650},
        {"id": "ST-02", "name": "Cherrapunji Escarpment", "state": "Meghalaya", "lat": 25.2700, "lon": 91.7300, "elevation": 1430},
        {"id": "ST-03", "name": "Tawang Pass Incline", "state": "Arunachal Pradesh", "lat": 27.5860, "lon": 91.8594, "elevation": 2900},
        {"id": "ST-04", "name": "Joshimath Slope Sensor", "state": "Uttarakhand", "lat": 30.5564, "lon": 79.5664, "elevation": 1890},
        {"id": "ST-05", "name": "Kohima Bypass Cut", "state": "Nagaland", "lat": 25.6700, "lon": 94.1100, "elevation": 1440},
        {"id": "ST-06", "name": "Aizawl North Face", "state": "Mizoram", "lat": 23.7300, "lon": 92.7100, "elevation": 1130},
    ]

    @classmethod
    def get_stations(cls) -> List[Dict[str, Any]]:
        return cls.STATIONS

    @classmethod
    def generate_packet(
        cls,
        station_id: str = "ST-01",
        scenario: str = "Normal"
    ) -> Dict[str, Any]:
        """
        Generate a single telemetry packet with realistic sensor values.
        Scenarios: 'Normal', 'Monsoon Surge', 'Critical Slope Failure', 'Micro-Seismic Event'
        """
        station = next((s for s in cls.STATIONS if s["id"] == station_id), cls.STATIONS[0])
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if scenario == "Critical Slope Failure":
            rainfall = random.uniform(180.0, 260.0)
            rainfall_3d = random.uniform(350.0, 520.0)
            slope = random.uniform(42.0, 58.0)
            pore_pressure = random.uniform(140.0, 195.0)  # kPa
            soil_moisture = random.uniform(85.0, 96.0)    # %
            soil_saturation = soil_moisture / 100.0
            soil_strain = random.uniform(0.008, 0.015)
            acoustic_emission = random.uniform(75.0, 95.0)  # dB
            microseismic = random.uniform(0.70, 0.95)
        elif scenario == "Monsoon Surge":
            rainfall = random.uniform(90.0, 140.0)
            rainfall_3d = random.uniform(180.0, 280.0)
            slope = random.uniform(30.0, 40.0)
            pore_pressure = random.uniform(80.0, 120.0)
            soil_moisture = random.uniform(65.0, 80.0)
            soil_saturation = soil_moisture / 100.0
            soil_strain = random.uniform(0.003, 0.006)
            acoustic_emission = random.uniform(50.0, 68.0)
            microseismic = random.uniform(0.35, 0.55)
        elif scenario == "Micro-Seismic Event":
            rainfall = random.uniform(20.0, 50.0)
            rainfall_3d = random.uniform(60.0, 110.0)
            slope = random.uniform(32.0, 44.0)
            pore_pressure = random.uniform(40.0, 75.0)
            soil_moisture = random.uniform(40.0, 60.0)
            soil_saturation = soil_moisture / 100.0
            soil_strain = random.uniform(0.005, 0.009)
            acoustic_emission = random.uniform(80.0, 98.0)
            microseismic = random.uniform(0.80, 0.98)
        else:  # Normal
            rainfall = random.uniform(0.0, 25.0)
            rainfall_3d = random.uniform(10.0, 45.0)
            slope = random.uniform(15.0, 28.0)
            pore_pressure = random.uniform(20.0, 50.0)
            soil_moisture = random.uniform(25.0, 45.0)
            soil_saturation = soil_moisture / 100.0
            soil_strain = random.uniform(0.0005, 0.002)
            acoustic_emission = random.uniform(25.0, 45.0)
            microseismic = random.uniform(0.05, 0.25)

        return {
            "timestamp": now,
            "station_id": station["id"],
            "station_name": station["name"],
            "location": station["state"],
            "lat": station["lat"],
            "lon": station["lon"],
            "elevation_m": station["elevation"],
            "scenario": scenario,
            "Rainfall_mm": round(rainfall, 1),
            "Rainfall_3Day": round(rainfall_3d, 1),
            "Rainfall_7Day": round(rainfall_3d * 1.5, 1),
            "Slope_Angle": round(slope, 1),
            "slope_degree": round(slope, 1),
            "soil_moisture_percent": round(soil_moisture, 1),
            "Soil_Saturation": round(soil_saturation, 3),
            "Pore_Water_Pressure_kPa": round(pore_pressure, 1),
            "Soil_Strain": round(soil_strain, 6),
            "Acoustic_Emission_dB": round(acoustic_emission, 1),
            "Microseismic_Activity": round(microseismic, 3),
            "Temperature_C": round(random.uniform(12.0, 22.0), 1),
            "Humidity_percent": round(random.uniform(55.0, 95.0), 1),
            "Vegetation_Cover": round(random.uniform(0.3, 0.8), 2),
            "NDVI_Index": round(random.uniform(0.3, 0.75), 2),
            "TDR_Reflection_Index": round(random.uniform(0.5, 1.2), 3),
            "Soil_Temperature_C": round(random.uniform(14.0, 20.0), 1),
        }
