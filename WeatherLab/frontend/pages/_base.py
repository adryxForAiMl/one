"""Shared layout and input handling for numerical method pages."""
import customtkinter as ctk
from tkinter import messagebox

from backend.exceptions import WeatherLabError
from frontend.components.cards import card
from frontend.components.graph_panel import GraphPanel
from frontend.components.input_fields import labeled_entry
from frontend.components.result_panel import ResultPanel
from frontend.theme import TEXT, MUTED, ACCENT
from utils.logger import get_logger

logger = get_logger(__name__)


class MethodPage(ctk.CTkFrame):
    def __init__(self, parent, title, description, fields, handler, method_note,
                 form_heading="NUMERICAL WORKBENCH", result_heading="RESULT",
                 reset_label="Reset", show_form_intro=True, result_size=22,
                 result_icon=None, show_hints=True, show_method_note=True,
                 result_unit=None):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure(0, weight=0, minsize=310)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        form = ctk.CTkScrollableFrame(self, width=310, fg_color="#0B0F12",
                                      corner_radius=16, border_width=1,
                                      border_color="#292B2E",
                                      scrollbar_button_color="#553018",
                                      scrollbar_button_hover_color="#7A431F")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        ctk.CTkLabel(form, text=form_heading, text_color=ACCENT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(20, 15))
        if show_form_intro:
            ctk.CTkLabel(form, text=title, text_color=TEXT, justify="left", anchor="w",
                         font=ctk.CTkFont(size=24, weight="bold")).pack(fill="x", pady=(0, 6))
            ctk.CTkLabel(form, text=description, text_color=MUTED, justify="left", anchor="w",
                         wraplength=285, font=ctk.CTkFont(size=12)).pack(fill="x", pady=(0, 20))
        self.entries = {}
        for name, label, default, hint in fields:
            if name == "__select__":
                ctk.CTkLabel(form, text=label, text_color=TEXT,
                             font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(0, 6))
                widget = ctk.CTkOptionMenu(form, values=default, height=39,
                                           fg_color="#191A1C", button_color="#7A3A12",
                                           button_hover_color="#A95117")
                widget.pack(fill="x", padx=18, pady=(0, 14))
                self.entries[name] = widget
            else:
                field = labeled_entry(form, label, default, hint if show_hints else None)
                field.pack(fill="x", padx=18, pady=(0, 14))
                self.entries[name] = field.entry
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(4, 14))
        ctk.CTkButton(actions, text="Calculate  →", height=42, corner_radius=9,
                      fg_color="#D9550A", hover_color="#F06D1D", text_color=TEXT,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: self.run(handler)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(actions, text=reset_label, height=42, corner_radius=9,
                      fg_color="#202124", hover_color="#303236", text_color=TEXT,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self.reset).pack(side="left", fill="x", expand=True, padx=(5, 0))
        if show_method_note:
            ctk.CTkLabel(form, text=method_note, text_color=MUTED, justify="left",
                         wraplength=280, font=ctk.CTkFont(size=11)).pack(fill="x", padx=18, pady=(4, 10))

        right = ctk.CTkFrame(self, fg_color="transparent")
        self.right = right
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        output = card(right)
        self.output = output
        output.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.result = ResultPanel(output, value_size=result_size, icon=result_icon)
        self.result_unit = result_unit
        self.result.heading.configure(text=result_heading)
        self.result.pack(fill="x", padx=20, pady=18)
        self.graph_host = ctk.CTkFrame(right, fg_color="transparent")
        self.graph_host.grid(row=1, column=0, sticky="nsew")
        self.graph_host.grid_columnconfigure(0, weight=1)
        self.graph_host.grid_rowconfigure(0, weight=1)
        self.graphs = [GraphPanel(self.graph_host)]
        self.graphs[0].grid(row=0, column=0, sticky="nsew")
        self.defaults = {name: default for name, _, default, _ in fields}

    def reset(self):
        for name, widget in self.entries.items():
            default = self.defaults[name]
            if name == "__select__":
                widget.set(default[0])
            else:
                widget.delete(0, "end")
                widget.insert(0, default)
        self.result.set_value("Ready when you are")
        self.result.detail.configure(text="Enter values and run the method.")
        self.result.set_table()
        self.right.grid_rowconfigure(0, weight=0)
        self.right.grid_rowconfigure(1, weight=1)
        self.output.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.graph_host.grid()
        self.graphs[0].grid(row=0, column=0, columnspan=2, sticky="nsew")
        for graph in self.graphs[1:]:
            graph.grid_remove()
        for graph in self.graphs:
            graph.draw_message("Choose a method to see its visual output.")

    def run(self, handler):
        values = {name: widget.get().strip() for name, widget in self.entries.items()}
        try:
            response = handler(values)
            headline, detail, plot = response[:3]
            table = response[3] if len(response) > 3 else None
            self.result.set_value(headline, self.result_unit)
            self.result.detail.configure(text=detail)
            self.result.set_table(table)
            charts = plot.get("charts", []) if isinstance(plot, dict) else ([plot] if plot else [])
            if charts:
                self.right.grid_rowconfigure(0, weight=0)
                self.right.grid_rowconfigure(1, weight=1)
                self.output.grid(row=0, column=0, sticky="ew", pady=(0, 14))
                self.graph_host.grid()
            else:
                self.right.grid_rowconfigure(0, weight=0)
                self.right.grid_rowconfigure(1, weight=1)
                self.output.grid(row=0, column=0, sticky="new")
                self.graph_host.grid_remove()
            while len(self.graphs) < max(1, len(charts)):
                graph = GraphPanel(self.graph_host)
                self.graphs.append(graph)
            for index, graph in enumerate(self.graphs):
                if index < len(charts):
                    graph.grid(row=0, column=index, sticky="nsew", padx=(0, 8) if index == 0 and len(charts) > 1 else (8, 0) if index else 0)
                    self.graph_host.grid_columnconfigure(index, weight=1)
                    chart = charts[index]
                    xs, ys, title, points, *options = chart
                    shade = options[0] if options else False
                    x_label = options[1] if len(options) > 1 else "x"
                    y_label = options[2] if len(options) > 2 else "y"
                    estimate = options[3] if len(options) > 3 else None
                    log_y = options[4] if len(options) > 4 else False
                    panel_title = options[5] if len(options) > 5 else "VISUALIZATION"
                    y_limits = options[6] if len(options) > 6 else None
                    graph.draw_series(xs, ys, title, points, shade, x_label, y_label,
                                      estimate, log_y, panel_title, y_limits)
                elif index == 0 and charts:
                    graph.grid(row=0, column=0, columnspan=2, sticky="nsew")
                    graph.draw_message("Calculation complete. No chart is needed for this result.")
                else:
                    graph.grid_remove()
        except (ValueError, ArithmeticError, WeatherLabError) as exc:
            logger.info("Rejected calculation input on %s: %s", self.__class__.__name__, exc)
            messagebox.showerror("Check your inputs", str(exc), parent=self.winfo_toplevel())
        except Exception:
            logger.exception("Unexpected programming error in numerical page")
            raise
