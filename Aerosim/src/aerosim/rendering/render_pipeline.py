from dataclasses import dataclass
from typing import Tuple


@dataclass
class CameraPreset:
    name: str
    distance: float
    height: float
    pitch_offset: float


CAMERA_PRESETS = {
    "chase": CameraPreset(name="Chase Follow", distance=4.5, height=1.8, pitch_offset=-5.0),
    "fpv": CameraPreset(name="FPV Gimbal Nose", distance=0.2, height=0.0, pitch_offset=-15.0),
    "orbit": CameraPreset(name="Orbit Free", distance=6.0, height=3.0, pitch_offset=-20.0),
    "top_down": CameraPreset(name="Nadir 90 Deg", distance=25.0, height=25.0, pitch_offset=-90.0),
}


class RenderPipeline:
    """Manages scene rendering parameters and camera viewpoints."""
    def __init__(self):
        self.active_camera = "chase"
        self.presets = CAMERA_PRESETS

    def set_camera(self, name: str) -> bool:
        if name in self.presets:
            self.active_camera = name
            return True
        return False

    def get_active_preset(self) -> CameraPreset:
        return self.presets[self.active_camera]
