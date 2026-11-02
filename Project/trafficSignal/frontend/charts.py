"""Embedded Matplotlib analytics charts for CustomTkinter dashboard.

Visualizes:
1. Real-time and comparative queue length evolution.
2. Cumulative delay trajectories integrated via the Composite Trapezoidal Rule.
3. Summary bar comparison (Average Waiting Time, Peak Queue, Delay Reduction %).
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, List, Dict
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as ticker
from Traffic.config.tokens import COLORS


DARK_BG = COLORS["surface_subtle"]
PANEL_BG = COLORS["surface"]
TEXT_COLOR = COLORS["navy"]
GRID_COLOR = COLORS["grid"]
COLOR_BASELINE = COLORS["red"]
COLOR_ADAPTIVE = COLORS["green"]
COLOR_ACCENT = COLORS["primary"]


class TrafficChartsPanel:
    """Matplotlib chart canvas container embedded in a CustomTkinter / Tkinter frame."""

    def __init__(self, parent_frame: tk.Widget):
        self.parent = parent_frame
        
        # Configure Matplotlib dark styling
        self.fig = Figure(figsize=(7.5, 5.0), dpi=100, facecolor=PANEL_BG)
        self.fig.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.12, hspace=0.38)
        
        # Subplot 1: Instantaneous Queue Length
        self.ax_queue = self.fig.add_subplot(2, 1, 1, facecolor=DARK_BG)
        # Subplot 2: Cumulative Trapezoidal Delay
        self.ax_delay = self.fig.add_subplot(2, 1, 2, facecolor=DARK_BG)
        
        self._style_axis(self.ax_queue, title="Instantaneous Queue Length (Vehicles)", ylabel="Queue (veh)")
        self._style_axis(self.ax_delay, title="Accumulated Delay via Trapezoidal Rule (veh·s)", xlabel="Simulation Time (s)", ylabel="Delay (veh·s)")

        # Persistent plotting lines for live streaming
        self.line_live_queue, = self.ax_queue.plot([], [], color=COLOR_ACCENT, lw=2.0, label="Live Queue")
        self.line_live_delay, = self.ax_delay.plot([], [], color=COLOR_ADAPTIVE, lw=2.0, label="Live Delay")
        
        self.ax_queue.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper right")
        self.ax_delay.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper left")

        # Tkinter Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        self.time_buffer: List[float] = []
        self.queue_buffer: List[float] = []
        self.delay_buffer: List[float] = []
        self.fixed_queue_buffer: List[float] = []
        self.adaptive_queue_buffer: List[float] = []
        self.fixed_delay_buffer: List[float] = []
        self.adaptive_delay_buffer: List[float] = []
        self.pair_mode = False

    def _style_axis(self, ax, title: str, xlabel: str = "", ylabel: str = ""):
        """Apply sleek dark theme styling to Matplotlib axes."""
        ax.set_title(title, color=TEXT_COLOR, fontsize=10, fontweight="bold", pad=6)
        if xlabel:
            ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=9)
        if ylabel:
            ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=9)
            
        ax.tick_params(colors=TEXT_COLOR, labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.35, color=GRID_COLOR)
        for spine in ax.spines.values():
            spine.set_color(GRID_COLOR)

    def reset(self):
        """Clear dynamic data buffers and reset axes."""
        self.time_buffer.clear()
        self.queue_buffer.clear()
        self.delay_buffer.clear()
        self.fixed_queue_buffer.clear()
        self.adaptive_queue_buffer.clear()
        self.fixed_delay_buffer.clear()
        self.adaptive_delay_buffer.clear()
        self.pair_mode = False
        
        self.ax_queue.cla()
        self.ax_delay.cla()
        
        self._style_axis(self.ax_queue, title="Instantaneous Queue Length (Vehicles)", ylabel="Queue (veh)")
        self._style_axis(self.ax_delay, title="Accumulated Delay via Trapezoidal Rule (veh·s)", xlabel="Simulation Time (s)", ylabel="Delay (veh·s)")
        
        self.line_live_queue, = self.ax_queue.plot([], [], color=COLOR_ACCENT, lw=2.0, label="Live Queue")
        self.line_live_delay, = self.ax_delay.plot([], [], color=COLOR_ADAPTIVE, lw=2.0, label="Live Delay")
        
        self.canvas.draw_idle()

    def update_live_step(self, t: float, queue: float, delay: float):
        """Append step telemetry point and refresh canvas."""
        self.time_buffer.append(t)
        self.queue_buffer.append(queue)
        self.delay_buffer.append(delay)

        self.line_live_queue.set_data(self.time_buffer, self.queue_buffer)
        self.line_live_delay.set_data(self.time_buffer, self.delay_buffer)

        # Rescale axes dynamically
        self.ax_queue.relim()
        self.ax_queue.autoscale_view()
        self.ax_delay.relim()
        self.ax_delay.autoscale_view()

        self.canvas.draw_idle()

    def update_pair_step(self, fixed, adaptive):
        """Update synchronized fixed/adaptive curves from real SUMO telemetry."""
        if not self.pair_mode:
            self.line_live_queue.remove()
            self.line_live_delay.remove()
            self.line_fixed_queue, = self.ax_queue.plot([], [], color=COLOR_BASELINE, lw=1.8, label="Fixed live")
            self.line_adaptive_queue, = self.ax_queue.plot([], [], color=COLOR_ADAPTIVE, lw=2.0, label="Adaptive live")
            self.line_fixed_delay, = self.ax_delay.plot([], [], color=COLOR_BASELINE, lw=1.8, label="Fixed live", linestyle="--")
            self.line_adaptive_delay, = self.ax_delay.plot([], [], color=COLOR_ADAPTIVE, lw=2.0, label="Adaptive live")
            self.ax_queue.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper right")
            self.ax_delay.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper left")
            self.pair_mode = True

        self.time_buffer.append(float(adaptive.time))
        self.fixed_queue_buffer.append(float(fixed.total_queue))
        self.adaptive_queue_buffer.append(float(adaptive.total_queue))
        self.fixed_delay_buffer.append(float(fixed.accumulated_delay))
        self.adaptive_delay_buffer.append(float(adaptive.accumulated_delay))
        self.line_fixed_queue.set_data(self.time_buffer, self.fixed_queue_buffer)
        self.line_adaptive_queue.set_data(self.time_buffer, self.adaptive_queue_buffer)
        self.line_fixed_delay.set_data(self.time_buffer, self.fixed_delay_buffer)
        self.line_adaptive_delay.set_data(self.time_buffer, self.adaptive_delay_buffer)
        self.ax_queue.relim()
        self.ax_queue.autoscale_view()
        self.ax_delay.relim()
        self.ax_delay.autoscale_view()
        self.canvas.draw_idle()

    def render_comparison(self, baseline_df: pd.DataFrame, adaptive_df: pd.DataFrame):
        """Render side-by-side before-versus-after curves on both subplots."""
        self.ax_queue.cla()
        self.ax_delay.cla()

        self._style_axis(self.ax_queue, title="Comparative Queue Length: Fixed Baseline vs Adaptive Optimization", ylabel="Queue (veh)")
        self._style_axis(self.ax_delay, title="Cumulative Delay Trajectory (Trapezoidal Integration \u222b q dt)", xlabel="Simulation Time (s)", ylabel="Delay (veh·s)")

        if not baseline_df.empty:
            self.ax_queue.plot(
                baseline_df["time"], baseline_df["total_queue"],
                color=COLOR_BASELINE, lw=1.8, label="Fixed Baseline", alpha=0.85
            )
            self.ax_delay.plot(
                baseline_df["time"], baseline_df["accumulated_delay"],
                color=COLOR_BASELINE, lw=2.0, label="Fixed Baseline", linestyle="--"
            )

        if not adaptive_df.empty:
            self.ax_queue.plot(
                adaptive_df["time"], adaptive_df["total_queue"],
                color=COLOR_ADAPTIVE, lw=2.0, label="Adaptive Optimized"
            )
            self.ax_delay.plot(
                adaptive_df["time"], adaptive_df["accumulated_delay"],
                color=COLOR_ADAPTIVE, lw=2.2, label="Adaptive Optimized"
            )

        self.ax_queue.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper right")
        self.ax_delay.legend(facecolor=PANEL_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, loc="upper left")

        self.canvas.draw_idle()
