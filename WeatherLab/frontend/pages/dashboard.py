"""Method overview dashboard."""
import customtkinter as ctk
from frontend.components.cards import card
from frontend.theme import TEXT, MUTED, ACCENT


def build(parent):
    page = ctk.CTkFrame(parent, fg_color="transparent")
    page.grid_columnconfigure((0, 1), weight=1)
    ctk.CTkLabel(page, text="A clearer way to explore\nnumerical methods.",
                 text_color=TEXT, justify="left", font=ctk.CTkFont(size=34, weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 8))
    ctk.CTkLabel(page, text="Choose a workspace, enter your data, and see each method in action.",
                 text_color=MUTED, font=ctk.CTkFont(size=14)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 24))
    tiles = [("01", "Interpolation", "Estimate values from known data."), ("02", "Root finding", "Solve f(x) = 0 and inspect convergence."),
             ("03", "Linear systems", "Solve simultaneous equations."), ("04", "Calculus", "Explore integration and differentiation."),
             ("05", "ODEs", "Approximate initial value problems."), ("06", "Data models", "Fit curves and interpolate with splines.")]
    for i, (number, title, detail) in enumerate(tiles):
        tile = card(page)
        tile.grid(row=2 + i // 2, column=i % 2, sticky="nsew", padx=(0, 12) if i % 2 == 0 else (0, 0), pady=6)
        ctk.CTkLabel(tile, text=number, text_color=ACCENT, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=18, pady=(17, 7))
        ctk.CTkLabel(tile, text=title, text_color=TEXT, font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=18)
        ctk.CTkLabel(tile, text=detail, text_color=MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=18, pady=(5, 18))
    return page
