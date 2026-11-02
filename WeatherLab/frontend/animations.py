"""Small non-blocking animation helpers."""


def fade_text(widget, text, steps=8, delay=18):
    """Reveal status text with a subtle character-by-character effect."""
    widget.configure(text="")
    def reveal(index=1):
        widget.configure(text=text[:index])
        if index < len(text):
            widget.after(delay, reveal, index + 1)
    if text:
        widget.after(0, reveal)
