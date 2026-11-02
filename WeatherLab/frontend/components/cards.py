"""Reusable surface card helpers."""
import customtkinter as ctk
from frontend.theme import SURFACE, BORDER


def card(parent, **kwargs):
    return ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=16,
                        border_width=1, border_color=BORDER, **kwargs)
