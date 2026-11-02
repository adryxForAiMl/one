"""Learning path with truthful module status and direct workspace navigation."""
import customtkinter as ctk

from frontend.components.cards import card
from frontend.theme import TEXT, MUTED, ACCENT


LEARNING_STEPS = (
    ("01", "Interpolation Lab",
     "Begin with known data points and estimate values between them.", "interpolation"),
    ("02", "Root Finding Lab",
     "Solve f(x) = 0 and compare bracketing with open methods.", "root_finding"),
    ("03", "Linear Systems Lab",
     "Solve Ax = b with pivoted direct and iterative methods.", "linear_systems"),
    ("04", "Numerical Integration",
     "Approximate definite integrals and compare quadrature rules.", "integration"),
    ("05", "Differential Equations",
     "Advance an initial value problem with Euler, Heun, and RK4.", "differential_equations"),
    ("06", "Curve Fitting Lab",
     "Fit least-squares polynomial models and evaluate R².", "curve_fitting"),
    ("07", "Spline Interpolation",
     "Build piecewise interpolants through ordered data points.", "spline"),
    ("08", "Learning Roadmap",
     "Review the available workspaces and recommended sequence.", "roadmap"),
)

EXTRA_MODULES = (
    ("+", "Numerical Differentiation",
     "Estimate derivatives with forward, backward, central, and five-point formulas.",
     "differentiation"),
)


def _module_row(parent, number, title, description, page_key, on_navigate,
                available_pages, current=False):
    available = page_key in available_pages
    status = "CURRENT" if current else "READY" if available else "UNAVAILABLE"
    row = card(parent)
    row.pack(fill="x", pady=5)
    ctk.CTkLabel(row, text=number, width=42, text_color=ACCENT,
                 font=ctk.CTkFont(size=17, weight="bold")).pack(
                     side="left", padx=(16, 10), pady=14)
    detail = ctk.CTkFrame(row, fg_color="transparent")
    detail.pack(side="left", fill="x", expand=True, pady=12)
    ctk.CTkLabel(detail, text=title, text_color=TEXT,
                 font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
    ctk.CTkLabel(detail, text=description, text_color=MUTED,
                 justify="left", wraplength=650,
                 font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(3, 0))

    if on_navigate and available and not current:
        ctk.CTkButton(row, text="Open  →", width=92, height=32,
                      fg_color="#9B3A05", hover_color="#C04B08",
                      text_color=TEXT,
                      command=lambda key=page_key: on_navigate(key)).pack(
                          side="right", padx=(8, 14))
    ctk.CTkLabel(row, text=status, text_color=ACCENT if available else MUTED,
                 width=82, font=ctk.CTkFont(size=9, weight="bold")).pack(
                     side="right", padx=(4, 8))
    return row


def build(parent, on_navigate=None):
    """Build a scrollable, ordered path and show only real page availability."""
    from frontend.pages import PAGE_REGISTRY

    page = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    ctk.CTkLabel(page, text="Learning Roadmap", text_color=TEXT,
                 font=ctk.CTkFont(size=28, weight="bold")).pack(
                     anchor="w", pady=(5, 4))
    ctk.CTkLabel(
        page,
        text="Follow the recommended order, or open any ready workspace directly.",
        text_color=MUTED, justify="left",
    ).pack(anchor="w", pady=(0, 18))

    for number, title, description, page_key in LEARNING_STEPS:
        _module_row(page, number, title, description, page_key, on_navigate,
                    PAGE_REGISTRY, current=page_key == "roadmap")

    ctk.CTkLabel(page, text="ADDITIONAL WORKSPACE", text_color=ACCENT,
                 font=ctk.CTkFont(size=10, weight="bold")).pack(
                     anchor="w", pady=(18, 5))
    for number, title, description, page_key in EXTRA_MODULES:
        _module_row(page, number, title, description, page_key, on_navigate,
                    PAGE_REGISTRY)
    return page
