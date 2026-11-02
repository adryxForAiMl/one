"""WeatherLab desktop window and top-level page routing."""
import random
from pathlib import Path
import customtkinter as ctk

from frontend.animations import fade_text
from frontend.components.sidebar import Sidebar
from frontend.navigation import NAV_ITEMS, build_page
from frontend.scrolling import install_wheel_scrolling
from frontend.theme import BG, TEXT, MUTED, BORDER, ACCENT
from utils.constants import APP_NAME, APP_SUBTITLE


class WeatherLab(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(str(Path(__file__).with_name("orange_theme.json")))
        self.title(f"{APP_NAME} | {APP_SUBTITLE}")
        self.geometry("1380x850")
        self.minsize(1100, 760)
        self.configure(fg_color=BG)
        self.stars = []
        self._closing = False
        self._animation_id = None
        self._resize_id = None

        self.protocol("WM_DELETE_WINDOW", self._close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = Sidebar(self, NAV_ITEMS, self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.configure(height=86)
        header.grid_propagate(False)
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(8, 12))
        header.grid_columnconfigure(0, weight=1)
        self.star_canvas = ctk.CTkCanvas(header, bg=BG, highlightthickness=0, bd=0)
        self.star_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.tk.call("lower", self.star_canvas._w)
        self.star_canvas.bind("<Configure>", self._schedule_static_stars)
        self.page_title = ctk.CTkLabel(header, text="", text_color=TEXT,
                                       font=ctk.CTkFont(size=27, weight="bold"))
        self.page_title.grid(row=0, column=0, sticky="w")
        self.page_subtitle = ctk.CTkLabel(header, text="", text_color=MUTED,
                                          font=ctk.CTkFont(size=12))
        self.page_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.status = ctk.CTkLabel(header, text="PYTHON  ·  SCIENTIFIC COMPUTING",
                                   text_color=ACCENT,
                                   font=ctk.CTkFont(size=9, weight="bold"))
        self.status.grid(row=0, column=1, rowspan=2, sticky="e")
        ctk.CTkFrame(self.main, height=1, fg_color=BORDER).grid(
            row=0, column=0, sticky="sew", padx=32
        )

        self.host = ctk.CTkFrame(self.main, fg_color="transparent")
        self.host.grid(row=1, column=0, sticky="nsew", padx=32, pady=(8, 20))
        self.host.grid_columnconfigure(0, weight=1)
        self.host.grid_rowconfigure(0, weight=1)
        self.current_page = None
        self.show_page("interpolation")
        self._animation_id = self.after(80, self.animate_stars)

    def show_page(self, key):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = build_page(key, self.host, self.show_page)
        self.current_page.grid(row=0, column=0, sticky="nsew")
        install_wheel_scrolling(self, self.current_page)
        titles = dict((item[0], item[1]) for item in NAV_ITEMS)
        subtitles = {
            "interpolation": "Estimate missing weather readings with numerical methods.",
            "root_finding": "Find the roots of equations using numerical methods.",
            "linear_systems": "Solve systems of linear equations using numerical methods.",
            "integration": "Approximate definite integrals using numerical methods.",
            "differentiation": "Estimate derivatives from function values.",
            "differential_equations": "Solve ordinary differential equations numerically.",
            "curve_fitting": "Fit data using least squares regression.",
            "spline": "Interpolate smoothly between ordered data points.",
            "roadmap": "Explore the numerical methods in WeatherLab.",
            "dashboard": "Numerical intelligence for scientific data analysis.",
        }
        self.page_title.configure(text=titles.get(key, "Numerical Differentiation" if key == "differentiation" else key.replace("_", " ").title()))
        self.page_subtitle.configure(text=subtitles[key])
        self.sidebar.select(key)
        fade_text(self.status, "PYTHON  ·  SCIENTIFIC COMPUTING")

    def animate_stars(self):
        if self._closing or not self.winfo_exists():
            return
        width = max(self.star_canvas.winfo_width(), 1)
        height = max(self.star_canvas.winfo_height(), 1)
        moving = []
        for x, y, speed, length, items in self.stars:
            x -= speed * .55
            y += speed
            if y < height + 30 and x > -length - 30:
                self.star_canvas.coords(items[0], x - length, y - length * .65, x, y)
                self.star_canvas.coords(items[1], x - length * .65, y - length * .4, x, y)
                self.star_canvas.coords(items[2], x - 2, y - 2, x + 2, y + 2)
                moving.append((x, y, speed, length, items))
            else:
                for item in items:
                    self.star_canvas.delete(item)
        self.stars = moving
        if len(self.stars) < 3 and random.random() < .2:
            self._create_meteor(width, height)
        self._animation_id = self.after(60, self.animate_stars)

    def _create_meteor(self, width, height):
        x = random.randint(max(1, width // 2), width + 70)
        y = random.randint(-20, max(1, height // 2))
        speed, length = random.randint(6, 10), random.randint(42, 82)
        items = (
            self.star_canvas.create_line(x - length, y - length * .65, x, y,
                                         fill="#643619", width=7, capstyle="round", tags="meteor"),
            self.star_canvas.create_line(x - length * .65, y - length * .4, x, y,
                                         fill=ACCENT, width=3, capstyle="round", tags="meteor"),
            self.star_canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                                         fill="#FFF0C2", outline="", tags="meteor"),
        )
        self.stars.append((x, y, speed, length, items))

    def _schedule_static_stars(self, _event=None):
        if self._closing:
            return
        if self._resize_id is not None:
            self.after_cancel(self._resize_id)
        self._resize_id = self.after(120, self._draw_static_stars)

    def _draw_static_stars(self):
        self._resize_id = None
        if self._closing:
            return
        self.star_canvas.delete("static-star")
        self.star_canvas.delete("meteor")
        width = max(self.star_canvas.winfo_width(), 1)
        height = max(self.star_canvas.winfo_height(), 1)
        self.stars = []
        for _ in range(30):
            x, y = random.randrange(width), random.randrange(height)
            radius = random.choice((1, 1, 1, 2))
            color = random.choice(("#493222", "#634026", "#73421F"))
            self.star_canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                         fill=color, outline="", tags="static-star")

    def _close(self):
        self._closing = True
        for job in (self._animation_id, self._resize_id):
            if job is not None:
                try:
                    self.after_cancel(job)
                except ctk.TclError:
                    pass
        self.destroy()
