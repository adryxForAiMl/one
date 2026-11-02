import json
from pathlib import Path
from typing import Dict, Any


DEFAULT_CONFIG: Dict[str, Any] = {
    "vehicle": {
        "type": "quadcopter_x",
        "mass_kg": 1.35,
        "arm_length_m": 0.24,
        "max_motor_rpm": 12000.0,
        "max_motor_thrust_n": 7.5,
        "battery": {
            "cell_count": 4,
            "capacity_mah": 3500.0,
            "nominal_voltage": 14.8,
            "max_voltage": 16.8
        }
    },
    "autopilot": {
        "takeoff_alt_m": 8.0,
        "rth_alt_m": 15.0,
        "max_tilt_deg": 35.0,
        "max_yaw_rate_deg_s": 90.0,
        "cruise_speed_m_s": 6.0
    },
    "failsafe": {
        "low_battery_percent": 20.0,
        "critical_battery_percent": 10.0,
        "action_on_low_battery": "RTH"
    }
}


class ConfigManager:
    """Manages AeroSim configuration loading, validation, and defaults."""
    def __init__(self, config_path: str | None = None):
        self.config = dict(DEFAULT_CONFIG)
        if config_path and Path(config_path).exists():
            self.load(config_path)

    def load(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._recursive_update(self.config, data)

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def _recursive_update(self, base: dict, new: dict):
        for k, v in new.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._recursive_update(base[k], v)
            else:
                base[k] = v

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        curr = self.config
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr
