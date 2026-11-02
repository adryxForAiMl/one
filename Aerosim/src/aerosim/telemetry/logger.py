import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from aerosim.interfaces import TelemetryInterface


class FlightDataLogger(TelemetryInterface):
    """
    High-frequency Blackbox Flight Data Recorder:
    - Records 50Hz timestamped telemetry frames
    - Exports to standard CSV / JSONL flight logs in data/logs/
    """
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.records: List[Dict[str, Any]] = []
        self.session_id = time.strftime("flight_%Y%m%d_%H%M%S")
        self.current_csv_file = self.log_dir / f"{self.session_id}.csv"

    def log(self, timestamp: float, data: Dict[str, Any]) -> None:
        pos = data.get("position", {})
        att = data.get("attitude", {})
        vel = data.get("velocity", {})
        bat = data.get("battery", {})
        gps = data.get("gps", {})
        motors = data.get("motors", {})

        flattened = {
            "timestamp": timestamp,
            "flight_mode": data.get("flight_mode", "UNKNOWN"),
            "is_armed": int(data.get("is_armed", False)),
            "alt_agl": pos.get("altitude_agl", 0.0),
            "alt_msl": pos.get("altitude_msl", 0.0),
            "lat": gps.get("latitude", 0.0),
            "lon": gps.get("longitude", 0.0),
            "roll": att.get("roll", 0.0),
            "pitch": att.get("pitch", 0.0),
            "yaw": att.get("yaw", 0.0),
            "speed": vel.get("groundspeed", 0.0),
            "climb": vel.get("climb_rate", 0.0),
            "battery_v": bat.get("voltage", 0.0),
            "battery_pct": bat.get("percentage", 0.0),
            "m1_rpm": motors.get("m1_rpm", 0),
            "m2_rpm": motors.get("m2_rpm", 0),
            "m3_rpm": motors.get("m3_rpm", 0),
            "m4_rpm": motors.get("m4_rpm", 0),
        }
        self.records.append(flattened)

    def export(self, filepath: str | None = None) -> bool:
        if not self.records:
            return False

        target_file = Path(filepath) if filepath else self.current_csv_file
        target_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(target_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = list(self.records[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.records)
            return True
        except Exception as e:
            print(f"[FlightDataLogger] Error exporting log: {e}")
            return False

    def get_summary(self) -> dict:
        if not self.records:
            return {"total_records": 0, "duration_s": 0.0}

        t_start = self.records[0]["timestamp"]
        t_end = self.records[-1]["timestamp"]
        return {
            "session_id": self.session_id,
            "total_records": len(self.records),
            "duration_s": round(t_end - t_start, 2),
            "file": str(self.current_csv_file)
        }
