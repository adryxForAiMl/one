"""Page navigation registry."""
from frontend.pages import PAGE_REGISTRY


NAV_ITEMS = [
    ("interpolation", "Interpolation Lab", "∿"),
    ("root_finding", "Root Finding Lab", "⌕"),
    ("linear_systems", "Linear Systems Lab", "▦"),
    ("integration", "Numerical Integration", "∫"),
    ("differential_equations", "Differential Equations", "⌁"),
    ("curve_fitting", "Curve Fitting Lab", "⌁"),
    ("spline", "Spline Interpolation", "⌇"),
    ("roadmap", "Learning Roadmap", "☷"),
]


def build_page(key, parent, on_navigate=None):
    if key == "roadmap":
        return PAGE_REGISTRY[key](parent, on_navigate)
    return PAGE_REGISTRY[key](parent)
