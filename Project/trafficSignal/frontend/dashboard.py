"""Dashboard control panel and KPI telemetry cards using CustomTkinter.

Provides:
- Real-time KPI Metric cards (Time, Active Vehicles, Mean Wait, Total Queue, Throughput)
- Simulation Mode Selector (Fixed Baseline, Adaptive Optimization, Head-to-Head Comparative Benchmark)
- SUMO-GUI animation launch toggle
- Signal timing constraints and demand sliders
- Simulation lifecycle controls (Start, Pause, Resume, Stop, Export CSV)
"""

from __future__ import annotations
import customtkinter as ctk
import tkinter as tk
from Traffic.config.tokens import COLORS
from typing import Callable, Optional, Dict, Any


class ToolTip:
    """Delayed tooltip for desktop controls."""

    def __init__(self, widget: Any, message: str):
        self.widget = widget
        self.message = message
        self.window = None
        self.after_id = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def schedule(self, _event=None):
        self.after_id = self.widget.after(500, self.show)

    def show(self):
        self.after_id = None
        if self.window or not self.message:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        tk.Label(self.window, text=self.message, justify="left", background=COLORS["navy"],
                 foreground=COLORS["surface"], padx=9, pady=6, relief="solid", borderwidth=1,
                 font=("Arial", 10)).pack()

    def hide(self, _event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.window:
            self.window.destroy()
            self.window = None


class MetricCard(ctk.CTkFrame):
    """Sleek KPI metric display card with title, value, and unit."""

    def __init__(
        self,
        master: Any,
        title: str,
        initial_value: str = "--",
        unit: str = "",
        accent_color: str = COLORS["primary"]
    ):
        super().__init__(master, fg_color=COLORS["surface"], corner_radius=10, border_width=1, border_color=COLORS["border"])
        self.accent_color = accent_color
        
        self.lbl_title = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["muted"]
        )
        self.lbl_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.lbl_value = ctk.CTkLabel(
            self, text=initial_value, font=ctk.CTkFont(size=20, weight="bold"), text_color=accent_color
        )
        self.lbl_value.pack(anchor="w", padx=12, pady=(0, 2))

        self.lbl_unit = ctk.CTkLabel(
            self, text=unit, font=ctk.CTkFont(size=10), text_color=COLORS["subtle"]
        )
        self.lbl_unit.pack(anchor="w", padx=12, pady=(0, 8))

    def update_value(self, value: str, unit: Optional[str] = None):
        self.lbl_value.configure(text=value)
        if unit is not None:
            self.lbl_unit.configure(text=unit)


class DashboardControls(ctk.CTkScrollableFrame):
    """Side control panel for simulation configuration, inputs, and actions."""

    def __init__(
        self,
        master: Any,
        on_start: Callable[[], None],
        on_pause: Callable[[], None],
        on_resume: Callable[[], None],
        on_stop: Callable[[], None],
        on_reset: Callable[[], None],
        on_export: Callable[[], None]
    ):
        super().__init__(master, fg_color=COLORS["surface_subtle"], corner_radius=12, width=320)
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_resume = on_resume
        self.on_stop = on_stop
        self.on_reset = on_reset
        self.on_export = on_export

        self._build_header()
        self._build_mode_selector()
        self._build_parameters_section()
        self._build_action_buttons()
        self._build_status_log()

    def _build_header(self):
        title = ctk.CTkLabel(
            self, text="🚦 Control Panel", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["navy"]
        )
        title.pack(anchor="w", padx=14, pady=(12, 6))

    def _build_mode_selector(self):
        lbl = ctk.CTkLabel(
            self, text="SIMULATION MODE", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"]
        )
        lbl.pack(anchor="w", padx=14, pady=(10, 2))

        self.mode_var = ctk.StringVar(value="Head-to-Head Comparative Benchmark")
        self.mode_menu = ctk.CTkOptionMenu(
            self,
            values=[
                "Head-to-Head Comparative Benchmark",
                "Adaptive Optimization (Proposed)",
                "Fixed-Time Baseline"
            ],
            variable=self.mode_var,
            fg_color=COLORS["border"],
            button_color=COLORS["primary_hover"],
            button_hover_color=COLORS["muted"],
            text_color=COLORS["navy"],
            dropdown_fg_color=COLORS["surface_subtle"],
            height=32
        )
        self.mode_menu.pack(fill="x", padx=14, pady=(0, 10))
        ToolTip(self.mode_menu, "Choose fixed control, adaptive control, or a sequential comparison.")

    def _build_parameters_section(self):
        # SUMO GUI Checkbox
        self.gui_var = ctk.BooleanVar(value=False)
        self.chk_gui = ctk.CTkCheckBox(
            self,
            text="Launch SUMO-GUI Animation",
            variable=self.gui_var,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["navy"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"]
        )
        self.chk_gui.pack(anchor="w", padx=14, pady=(4, 12))
        ToolTip(self.chk_gui, "Open SUMO-GUI while the simulation runs.")

        # Traffic Demand
        lbl_demand = ctk.CTkLabel(
            self, text="SEEDED TRAFFIC SCENARIO", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"]
        )
        lbl_demand.pack(anchor="w", padx=14, pady=(6, 2))

        self.demand_var = ctk.StringVar(value="Balanced")
        self.demand_menu = ctk.CTkOptionMenu(
            self,
            values=["Balanced", "Heavy North–South", "Sudden Surge", "Rush Hour"],
            variable=self.demand_var,
            fg_color=COLORS["border"],
            button_color=COLORS["primary_hover"],
            height=30
        )
        self.demand_menu.pack(fill="x", padx=14, pady=(0, 12))
        ToolTip(self.demand_menu, "Choose a seeded arrival pattern for this run.")

        # Simulation Duration
        self.lbl_dur = ctk.CTkLabel(
            self, text="Duration: 180 seconds", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]
        )
        self.lbl_dur.pack(anchor="w", padx=14, pady=(4, 2))
        
        self.slider_duration = ctk.CTkSlider(
            self, from_=30, to=600, number_of_steps=19,
            command=lambda v: self.lbl_dur.configure(text=f"Duration: {int(v)} seconds")
        )
        self.slider_duration.set(180)
        self.slider_duration.pack(fill="x", padx=14, pady=(0, 12))
        ToolTip(self.slider_duration, "Set the duration in simulation seconds.")

        # Cycle Length
        self.lbl_cycle = ctk.CTkLabel(
            self, text="Cycle Length: 90 seconds", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]
        )
        self.lbl_cycle.pack(anchor="w", padx=14, pady=(4, 2))
        
        self.slider_cycle = ctk.CTkSlider(
            self, from_=45, to=150, number_of_steps=21,
            command=lambda v: self.lbl_cycle.configure(text=f"Cycle Length: {int(v)} seconds")
        )
        self.slider_cycle.set(90)
        self.slider_cycle.pack(fill="x", padx=14, pady=(0, 14))
        ToolTip(self.slider_cycle, "Set the signal cycle length in seconds.")

    def _build_action_buttons(self):
        self.btn_start = ctk.CTkButton(
            self, text="▶  Run Simulation", fg_color=COLORS["green"], text_color=COLORS["page"],
            hover_color=COLORS["sky"], font=ctk.CTkFont(size=13, weight="bold"), height=36,
            command=self.on_start
        )
        self.btn_start.pack(fill="x", padx=14, pady=(6, 6))
        ToolTip(self.btn_start, "Start a live SUMO simulation with the selected settings.")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=4)

        self.btn_pause = ctk.CTkButton(
            btn_row, text="⏸ Pause", fg_color=COLORS["border"], hover_color=COLORS["primary_hover"],
            width=135, height=32, command=self.on_pause
        )
        self.btn_pause.pack(side="left", padx=(0, 4))
        ToolTip(self.btn_pause, "Pause the active run. Space toggles pause and resume.")

        self.btn_resume = ctk.CTkButton(
            btn_row, text="▶ Resume", fg_color=COLORS["surface"], hover_color=COLORS["surface_subtle"],
            text_color=COLORS["navy"], width=135, height=32, command=self.on_resume
        )
        self.btn_resume.pack(side="right", padx=(4, 0))
        ToolTip(self.btn_resume, "Resume a paused run. Space toggles pause and resume.")

        self.btn_stop = ctk.CTkButton(
            self, text="⏹ Stop", fg_color=COLORS["red"], hover_color=COLORS["red"],
            text_color=COLORS["surface"], height=32, command=self.on_stop
        )
        self.btn_stop.pack(fill="x", padx=14, pady=(2, 4))
        ToolTip(self.btn_stop, "Stop the active simulation and paired benchmark.")

        self.btn_reset = ctk.CTkButton(
            self, text="↺ Reset", fg_color=COLORS["surface"], hover_color=COLORS["surface_subtle"],
            text_color=COLORS["navy"], height=32, command=self.on_reset
        )
        self.btn_reset.pack(fill="x", padx=14, pady=(2, 4))
        ToolTip(self.btn_reset, "Stop the current run and clear displayed metrics. R does the same.")

        self.btn_export = ctk.CTkButton(
            self, text="💾 Export Results CSV", fg_color=COLORS["primary"], text_color=COLORS["page"],
            hover_color=COLORS["primary_hover"], font=ctk.CTkFont(size=12, weight="bold"), height=32,
            command=self.on_export
        )
        self.btn_export.pack(fill="x", padx=14, pady=(10, 10))
        ToolTip(self.btn_export, "Export available telemetry or comparison CSV and JSON files.")

    def _build_status_log(self):
        lbl = ctk.CTkLabel(
            self, text="SYSTEM STATUS & LOG", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["muted"]
        )
        lbl.pack(anchor="w", padx=14, pady=(10, 2))

        self.txt_status = ctk.CTkTextbox(
            self, height=120, fg_color=COLORS["page"], text_color=COLORS["muted"], font=ctk.CTkFont(size=10)
        )
        self.txt_status.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.log_message("System initialized. Ready.")

    def log_message(self, msg: str):
        self.txt_status.insert("end", f"> {msg}\n")
        self.txt_status.see("end")

    def get_settings(self) -> Dict[str, Any]:
        """Extract user configured simulation parameters."""
        scenario_name = {
            "Balanced": "balanced",
            "Heavy North–South": "heavy_ns",
            "Sudden Surge": "sudden_surge",
            "Rush Hour": "rush_hour",
        }.get(self.demand_var.get(), "balanced")
        vol_ns, vol_ew = 600, 450

        mode_raw = self.mode_var.get()
        if "Benchmark" in mode_raw:
            mode = "Benchmark"
        elif "Adaptive" in mode_raw:
            mode = "Adaptive_Optimized"
        else:
            mode = "Fixed_Baseline"

        return {
            "mode": mode,
            "use_gui": self.gui_var.get(),
            "duration": int(self.slider_duration.get()),
            "cycle_length": float(self.slider_cycle.get()),
            "vol_ns": vol_ns,
            "vol_ew": vol_ew,
            "scenario": scenario_name,
        }
