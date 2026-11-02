"""Consistent labeled input controls."""
import customtkinter as ctk
from frontend.theme import SURFACE, TEXT, MUTED, BORDER


def labeled_entry(parent, label, default="", hint=None):
    wrap = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(wrap, text=label, text_color=TEXT,
                 font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 6))
    entry = ctk.CTkEntry(wrap, height=39, corner_radius=8, fg_color="#080A0D",
                         border_color=BORDER, text_color=TEXT, placeholder_text_color=MUTED)
    entry.pack(fill="x")
    if default:
        entry.insert(0, default)
    if hint:
        ctk.CTkLabel(wrap, text=hint, text_color=MUTED,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(4, 0))
    wrap.entry = entry
    return wrap
