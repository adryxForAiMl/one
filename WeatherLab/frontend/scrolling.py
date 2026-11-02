"""Reliable trackpad and mouse-wheel scrolling for CustomTkinter pages."""
import sys


def install_wheel_scrolling(root, page):
    """Route wheel gestures to the scrollable frame under the pointer.

    CustomTkinter registers one global wheel callback per scrollable frame.
    Replacing those callbacks with one page-aware handler avoids competing
    handlers and makes macOS trackpad deltas behave consistently.
    """
    scroll_frames = []

    def collect(widget):
        try:
            import customtkinter as ctk
            if isinstance(widget, ctk.CTkScrollableFrame):
                scroll_frames.append(widget)
        except Exception:
            pass
        for child in widget.winfo_children():
            collect(child)

    collect(page)
    root.unbind_all("<MouseWheel>")
    root.unbind_all("<Button-4>")
    root.unbind_all("<Button-5>")

    def on_wheel(event):
        for scroll_frame in reversed(scroll_frames):
            try:
                if not scroll_frame.winfo_exists() or not scroll_frame._check_if_valid_scroll(event.widget):
                    continue
                canvas = scroll_frame._parent_canvas
                if canvas.yview() == (0.0, 1.0):
                    continue
                if event.num == 4:
                    amount = -3
                elif event.num == 5:
                    amount = 3
                elif sys.platform == "darwin":
                    # macOS trackpads send small, high-frequency deltas.
                    amount = -int(round(event.delta))
                else:
                    amount = -int(event.delta / 40) or (-1 if event.delta > 0 else 1)
                if amount:
                    canvas.yview_scroll(amount, "units")
                return "break"
            except (AttributeError, RuntimeError):
                continue
        return None

    root.bind_all("<MouseWheel>", on_wheel, add=True)
    root.bind_all("<Button-4>", on_wheel, add=True)
    root.bind_all("<Button-5>", on_wheel, add=True)
