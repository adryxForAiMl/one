"""Primary navigation sidebar."""
import customtkinter as ctk
from frontend.theme import SIDEBAR, TEXT, MUTED, ACCENT, ACCENT_DARK


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, pages, on_select):
        super().__init__(parent, width=245, corner_radius=0, fg_color=SIDEBAR)
        self.grid_propagate(False)
        self.pages = pages
        self.buttons = {}
        ctk.CTkLabel(self, text="✦  WeatherLab", text_color=ACCENT,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=22, pady=(28, 3))
        ctk.CTkLabel(self, text="NUMERICAL METHODS STUDIO", text_color=MUTED,
                     font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=23, pady=(0, 24))
        self.navigation = ctk.CTkFrame(self, fg_color="transparent")
        self.navigation.pack(fill="x")
        for key, title, icon in pages:
            button = ctk.CTkButton(self.navigation, text=f"{icon}   {title}", anchor="w", height=42,
                                   corner_radius=9, fg_color="transparent", hover_color="#2A1A10",
                                   text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"),
                                   command=lambda k=key: on_select(k))
            button.pack(fill="x", padx=12, pady=2)
            self.buttons[key] = button
        ctk.CTkFrame(self, height=1, fg_color="#292A2C").pack(fill="x", padx=18, pady=16)
        ctk.CTkLabel(self, text="CURRENT MODULE", text_color=MUTED,
                     font=ctk.CTkFont(size=9, weight="bold")).pack(anchor="w", padx=20)
        self.active_name = ctk.CTkLabel(self, text="Interpolation\nLab", text_color=TEXT,
                                        justify="left", anchor="w",
                                        font=ctk.CTkFont(size=15, weight="bold"))
        self.active_name.pack(anchor="w", padx=20, pady=(7, 2))
        self.active_number = ctk.CTkLabel(self, text="MODULE 01  ·  ACTIVE", text_color=ACCENT,
                                          font=ctk.CTkFont(size=9, weight="bold"))
        self.active_number.pack(anchor="w", padx=20)
        ctk.CTkLabel(self, text="PYTHON  ·  SCIENTIFIC COMPUTING", text_color="#667384",
                     font=ctk.CTkFont(size=9, weight="bold")).pack(side="bottom", anchor="w", padx=18, pady=20)

    def select(self, key):
        highlighted = "integration" if key == "differentiation" else key
        for page, button in self.buttons.items():
            active = page == highlighted
            button.configure(fg_color=ACCENT_DARK if active else "transparent",
                             text_color=TEXT)
        names = {page: title for page, title, _ in self.pages}
        title = names.get(key, key.replace("_", " ").title())
        if key == "interpolation":
            title = "Lagrange Interpolation"
        if key == "differentiation":
            title = "Numerical Differentiation"
        self.active_name.configure(text=title.replace(" ", "\n", 1))
        if highlighted in self.buttons:
            position = list(self.buttons).index(highlighted) + 1
            self.active_number.configure(text=f"MODULE {position:02d}  ·  ACTIVE")
