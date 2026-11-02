"""
Landslide_AI: Advanced Machine Learning & IoT Early Warning System
for Landslide Risk Prediction and Geotechnical Hazard Assessment.
"""

__version__ = "2.0.0"
__author__ = "Landslide AI Research Team"

from src.config import Config
from src.model import LandslidePredictor, WSNLandslidePredictor

__all__ = ["Config", "LandslidePredictor", "WSNLandslidePredictor"]
