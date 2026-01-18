"""
Left panel UI components for PANDA SCAN.
Contains diagnostics and log display.
"""
import tkinter as tk
from tkinter import ttk
from app.tk_app.core.config import LEFT_PANEL_WIDTH


class LeftPanel:
    """Manages the left diagnostics panel."""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.configure(width=LEFT_PANEL_WIDTH)
        self.frame.grid_propagate(False)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        """Build the panel UI components."""
        # Top section with title and status dots
        self.top_frame = ttk.Frame(self.frame)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ttk.Label(self.top_frame, text="SYSTEM DIAGNOSTICS")
        self.title_label.grid(row=0, column=0, sticky="w")

        self.dots_frame = ttk.Frame(self.top_frame)
        self.dots_frame.grid(row=0, column=1, sticky="e")

        self.dot1 = tk.Label(self.dots_frame, text="●", font=("Segoe UI", 12))
        self.dot2 = tk.Label(self.dots_frame, text="●", font=("Segoe UI", 12))
        self.dot1.pack(side="left", padx=(0, 6))
        self.dot2.pack(side="left")

        # Log area with scrollbar
        self.log_frame = ttk.Frame(self.frame)
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(self.log_frame, wrap="word", bd=0, highlightthickness=0)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scroll.grid(row=0, column=1, sticky="ns")

    def grid(self, **kwargs):
        """Grid the panel."""
        self.frame.grid(**kwargs)

    def apply_theme(self, theme_manager):
        """Apply theme to all components."""
        c = theme_manager.colors

        self.frame.configure(style="Card.TFrame")
        self.top_frame.configure(style="Card.TFrame")
        self.log_frame.configure(style="Card.TFrame")

        self.title_label.configure(foreground=c["muted"], background=c["card"], font=("Segoe UI Semibold", 10))

        self.dot1.configure(bg=c["card"], fg="#9CA3AF")
        self.dot2.configure(bg=c["card"], fg="#22C55E")

        theme_manager.configure_widget(self.log_text, "text")
