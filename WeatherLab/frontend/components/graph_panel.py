"""Reusable Matplotlib chart panel."""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from frontend.theme import SURFACE, TEXT, MUTED, BORDER, ACCENT


class GraphPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=SURFACE, corner_radius=16,
                         border_width=1, border_color=BORDER)
        self.heading = ctk.CTkLabel(self, text="VISUALIZATION", text_color=MUTED,
                                    font=ctk.CTkFont(size=10, weight="bold"))
        self.heading.pack(anchor="w", padx=18, pady=(15, 0))
        self.figure = Figure(figsize=(7, 3.1), dpi=100, facecolor=SURFACE)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self.draw_message("Choose a method to see its visual output.")

    def draw_message(self, message):
        self.axes.clear()
        self.axes.set_facecolor(SURFACE)
        self.axes.text(.5, .5, message, transform=self.axes.transAxes,
                       ha="center", va="center", color=MUTED, fontsize=10)
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def draw_series(self, xs, ys, title="Numerical result", points=None, shade=False,
                    x_label="x", y_label="y", estimate=None, log_y=False,
                    panel_title="VISUALIZATION", y_limits=None):
        self.axes.clear()
        self.heading.configure(text=panel_title)
        self.axes.set_facecolor(SURFACE)
        self.axes.plot(xs, ys, color=ACCENT, linewidth=2, label=title)
        if shade:
            self.axes.fill_between(xs, ys, 0, color=ACCENT, alpha=.18)
        if log_y:
            self.axes.set_yscale("log")
        if y_limits is not None:
            self.axes.set_ylim(*y_limits)
        if points:
            px, py = zip(*points)
            self.axes.scatter(px, py, color="#FF8428", zorder=4, label="Observed points")
        if estimate is not None:
            estimate_x, estimate_y = estimate
            self.axes.scatter([estimate_x], [estimate_y], marker="D", s=85,
                              color="#FFC36B", edgecolors=TEXT, linewidths=.8,
                              zorder=5, label="Estimated point")
            self.axes.annotate(f"{estimate_y:.3f}", (estimate_x, estimate_y),
                               xytext=(8, 9), textcoords="offset points",
                               color="#FFC36B", fontsize=9, weight="bold")
        self.axes.tick_params(colors=TEXT, labelsize=8)
        self.axes.set_xlabel(x_label, color=TEXT, fontsize=9)
        self.axes.set_ylabel(y_label, color=TEXT, fontsize=9)
        self.axes.grid(color=BORDER, linewidth=.6, alpha=.8)
        for spine in self.axes.spines.values():
            spine.set_color(BORDER)
        handles, labels = self.axes.get_legend_handles_labels()
        if handles:
            self.axes.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, 1.16),
                             ncol=min(3, len(handles)), facecolor=SURFACE,
                             edgecolor=BORDER, labelcolor=TEXT, fontsize=8)
        self.figure.subplots_adjust(left=.12, right=.98, bottom=.16, top=.79)
        self.canvas.draw_idle()
