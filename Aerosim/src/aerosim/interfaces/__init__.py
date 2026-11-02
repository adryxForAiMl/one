"""Abstract base classes and contracts for AeroSim components."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np


class SensorInterface(ABC):
    @abstractmethod
    def update(self, dt: float, state: Any) -> Dict[str, Any]:
        """Update sensor readings based on current vehicle state."""
        pass

    @abstractmethod
    def get_data(self) -> Dict[str, Any]:
        """Return the latest sensor reading dictionary."""
        pass


class ControllerInterface(ABC):
    @abstractmethod
    def update(self, dt: float) -> np.ndarray:
        """Compute and return motor or actuator commands."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal controller state."""
        pass


class TelemetryInterface(ABC):
    @abstractmethod
    def log(self, timestamp: float, data: Dict[str, Any]) -> None:
        """Log a telemetry data packet."""
        pass

    @abstractmethod
    def export(self, filepath: str) -> bool:
        """Export flight log to disk."""
        pass
