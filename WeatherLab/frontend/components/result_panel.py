"""Output surface used by all method pages."""
import customtkinter as ctk
from frontend.theme import TEXT, MUTED, ACCENT


class ResultPanel(ctk.CTkFrame):
    def __init__(self, parent, value_size=22, icon=None):
        super().__init__(parent, fg_color="transparent")
        self.heading = ctk.CTkLabel(self, text="RESULT", text_color=MUTED,
                                    font=ctk.CTkFont(size=10, weight="bold"))
        self.heading.pack(anchor="w")
        self.value_row = ctk.CTkFrame(self, fg_color="transparent")
        self.value_row.pack(anchor="w", pady=(8, 0))
        if icon == "thermometer":
            thermometer = ctk.CTkCanvas(self.value_row, width=34, height=48,
                                        bg="#111316", highlightthickness=0, bd=0)
            thermometer.pack(side="left", padx=(0, 12))
            thermometer.create_line(17, 7, 17, 31, fill=ACCENT, width=5, capstyle="round")
            thermometer.create_oval(8, 25, 26, 43, fill=ACCENT, outline=ACCENT)
            thermometer.create_line(17, 12, 17, 29, fill="#FFB56E", width=2, capstyle="round")
        self.value = ctk.CTkLabel(self.value_row, text="Ready when you are",
                                  text_color=TEXT, justify="left", anchor="w",
                                  wraplength=650,
                                  font=ctk.CTkFont(size=value_size, weight="bold"))
        self.value.pack(side="left", anchor="w")
        self.unit = ctk.CTkLabel(self.value_row, text="", text_color=ACCENT,
                                 font=ctk.CTkFont(size=value_size, weight="bold"))
        self.detail = ctk.CTkLabel(self, text="Enter values and run the method.",
                                   text_color=TEXT, justify="left", anchor="w",
                                   wraplength=650)
        self.detail.pack(anchor="w", pady=(5, 0))
        self.table = ctk.CTkTextbox(self, height=145, wrap="none", corner_radius=8,
                                    fg_color="#090A0C", border_width=1,
                                    border_color="#292A2C", text_color=TEXT,
                                    font=ctk.CTkFont(family="Menlo", size=10))

    def set_value(self, text, highlight_suffix=None):
        if highlight_suffix and text.endswith(highlight_suffix):
            self.value.configure(text=text[:-len(highlight_suffix)].rstrip())
            self.unit.configure(text=highlight_suffix)
            self.unit.pack(side="left", padx=(5, 0))
        else:
            self.unit.pack_forget()
            self.value.configure(text=text)

    def set_table(self, text=None):
        if text is None:
            self.table.pack_forget()
            return
        self.table.configure(state="normal")
        self.table.delete("1.0", "end")
        self.table.insert("1.0", text)
        self.table.configure(state="disabled")
        self.table.pack(fill="x", pady=(12, 0))
