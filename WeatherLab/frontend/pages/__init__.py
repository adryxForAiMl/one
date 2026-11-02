"""Registry of all user-facing workspaces."""
from frontend.pages.dashboard import build as dashboard
from frontend.pages.interpolation_page import build as interpolation
from frontend.pages.root_finding_page import build as root_finding
from frontend.pages.linear_systems_page import build as linear_systems
from frontend.pages.integration_page import build as integration
from frontend.pages.differentiation_page import build as differentiation
from frontend.pages.differential_equations_page import build as differential_equations
from frontend.pages.curve_fitting_page import build as curve_fitting
from frontend.pages.spline_page import build as spline
from frontend.pages.roadmap_page import build as roadmap

PAGE_REGISTRY = {
    "dashboard": dashboard,
    "interpolation": interpolation,
    "root_finding": root_finding,
    "linear_systems": linear_systems,
    "integration": integration,
    "differentiation": differentiation,
    "differential_equations": differential_equations,
    "curve_fitting": curve_fitting,
    "spline": spline,
    "roadmap": roadmap,
}
