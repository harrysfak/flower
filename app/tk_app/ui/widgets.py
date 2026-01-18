"""
Custom widget components for PANDA SCAN application.
"""
import tkinter as tk
from tkinter import ttk


class Scrollable(ttk.Frame):
    """Scrollable container with mousewheel support."""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._bind_mousewheel()

    def _on_frame_configure(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def _bind_mousewheel(self):
        def on_wheel(e):
            if e.delta:
                self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            else:
                if e.num == 4:
                    self.canvas.yview_scroll(-3, "units")
                elif e.num == 5:
                    self.canvas.yview_scroll(3, "units")

        self.canvas.bind_all("<MouseWheel>", on_wheel)
        self.canvas.bind_all("<Button-4>", on_wheel)
        self.canvas.bind_all("<Button-5>", on_wheel)


class StatusPill:
    """Status pill widget with rounded corners."""

    def __init__(self, parent, width=110, height=32):
        self.canvas = tk.Canvas(parent, width=width, height=height, bd=0, highlightthickness=0)
        self.width = width
        self.height = height
        self.text_id = None

    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

    def draw(self, text, colors, border_color):
        """Draw the pill with given text and colors."""
        from app.tk_app.core.utils import round_rect_points

        self.canvas.delete("all")
        r = 16

        points = round_rect_points(2, 2, self.width - 2, self.height - 2, r)
        self.canvas.create_polygon(points, smooth=True, fill=colors["pill"], outline=border_color)
        self.text_id = self.canvas.create_text(
            self.width // 2, self.height // 2,
            text=text,
            fill=colors["text"],
            font=("Segoe UI Semibold", 10)
        )

    def configure(self, **kwargs):
        self.canvas.configure(**kwargs)
