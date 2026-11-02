"""Global settings and configuration for the Adaptive Traffic Signal Optimization Simulator.
Provides system paths, signal timing constraints, numerical parameters, and SUMO binary discovery.
"""

from __future__ import annotations
import os
import shutil
import sys
from pathlib import Path
from dataclasses import dataclass, field

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
NETWORKS_DIR = DATA_DIR / "networks"
RESULTS_DIR = PROJECT_ROOT / "results"
TESTS_DIR = PROJECT_ROOT / "tests"

# Ensure runtime directories exist
NETWORKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def find_sumo_binary(gui: bool = False) -> str:
    """Locate the SUMO executable on macOS/Linux/Windows.
    Checks:
      1. Virtual environment bin directory (sys.prefix / 'bin')
      2. Workspace .venv directory
      3. SUMO_HOME environment variable
      4. sumolib.checkBinary resolution
      5. System PATH (via shutil.which)
      6. Standard macOS Homebrew locations (/opt/homebrew/bin, /usr/local/bin)
    """
    binary_name = "sumo-gui" if gui else "sumo"
    if sys.platform == "win32":
        binary_name += ".exe"

    # 1. Virtual environment bin (where pip installs binaries)
    venv_bin = Path(sys.prefix) / "bin" / binary_name
    if venv_bin.is_file() and os.access(venv_bin, os.X_OK):
        return str(venv_bin)

    workspace_venv_bin = PROJECT_ROOT.parent / ".venv" / "bin" / binary_name
    if workspace_venv_bin.is_file() and os.access(workspace_venv_bin, os.X_OK):
        return str(workspace_venv_bin)

    # 2. Environment variable SUMO_HOME
    sumo_home = os.environ.get("SUMO_HOME")
    if sumo_home:
        candidate = Path(sumo_home) / "bin" / binary_name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)

    # 3. sumolib checkBinary
    try:
        import sumolib
        return sumolib.checkBinary(binary_name)
    except Exception:
        pass

    # 4. System PATH
    found = shutil.which(binary_name)
    if found:
        return found

    # 4. Standard macOS Homebrew paths
    mac_paths = [
        Path("/opt/homebrew/bin") / binary_name,
        Path("/usr/local/bin") / binary_name,
        Path("/opt/homebrew/opt/sumo/bin") / binary_name,
    ]
    for p in mac_paths:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)

    # Fallback to binary name; will fail at execution time with helpful instructions
    return binary_name


@dataclass
class SignalTimingConfig:
    """Signal timing physical and safety constraints."""
    min_green: float = 10.0          # Minimum green time per phase (seconds)
    max_green: float = 60.0          # Maximum green time per phase (seconds)
    yellow_time: float = 4.0         # Transition yellow interval (seconds)
    all_red_time: float = 2.0        # Red clearance interval (seconds)
    min_cycle_length: float = 45.0   # Minimum allowable cycle length (seconds)
    max_cycle_length: float = 150.0  # Maximum allowable cycle length (seconds)
    default_cycle_length: float = 90.0  # Baseline fixed cycle length (seconds)
    lost_time_per_phase: float = 6.0    # yellow (4s) + all_red (2s) = 6s lost time


@dataclass
class SimulationConfig:
    """Simulation run parameters."""
    step_length: float = 1.0         # SUMO simulation step length in seconds
    default_duration: int = 300      # Default total simulation duration in seconds
    random_seed: int = 42            # Fixed seed for strictly reproducible experiments
    optimization_interval: int = 30  # Horizon / frequency of adaptive updates in seconds
    use_gui: bool = False            # Whether to launch sumo-gui or headless sumo
    time_delay_gui: int = 50         # Delay per step in ms when running SUMO-GUI
    junction_id: str = "junction_center"  # Central controlled traffic light junction


@dataclass
class DemandProfile:
    """Traffic demand characteristics."""
    name: str = "Medium"
    vehs_per_hour_ns: int = 600      # North-South volume (veh/h)
    vehs_per_hour_ew: int = 450      # East-West volume (veh/h)
    turning_ratio_left: float = 0.15 # Proportion turning left
    turning_ratio_right: float = 0.15# Proportion turning right
    saturation_flow_rate: float = 0.5# Saturation discharge capacity (veh/sec/lane ~= 1800 veh/h/lane)
    scenario: str = "balanced"       # balanced, heavy_ns, sudden_surge, rush_hour

    def __post_init__(self):
        if self.scenario not in {"balanced", "heavy_ns", "sudden_surge", "rush_hour"}:
            raise ValueError(f"Unsupported traffic scenario: {self.scenario}")
