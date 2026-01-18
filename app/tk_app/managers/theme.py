"""
Theme manager for PANDA SCAN application.
Handles all styling and theme switching.
"""
import tkinter as tk
from app.tk_app.core.config import LIGHT, DARK, STATUS_PILL_COLORS


class ThemeManager:
    """Manages application theme and styling."""

    def __init__(self, root, style):
        self.root = root
        self.style = style
        self.mode = "light"
        self.colors = LIGHT.copy()

        # Try to use clam theme
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

    def toggle_theme(self):
        """Switch between light and dark themes."""
        if self.mode == "light":
            self.mode = "dark"
            self.colors = DARK.copy()
        else:
            self.mode = "light"
            self.colors = LIGHT.copy()

    def get_pill_color(self, state):
        """Get the pill background color for a given state."""
        state_colors = STATUS_PILL_COLORS.get(state.upper(), STATUS_PILL_COLORS["IDLE"])
        return state_colors[self.mode]

    def apply_to_root(self):
        """Apply theme to root window."""
        self.root.configure(bg=self.colors["bg"])

    def apply_to_ttk(self):
        """Configure ttk styles."""
        c = self.colors

        self.style.configure("Card.TFrame", background=c["card"])
        self.style.configure("TFrame", background=c["card"])
        self.style.configure("TLabel", background=c["card"], foreground=c["text"], font=("Segoe UI", 11))
        self.style.configure("TButton", padding=(12, 7))

        self.style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), background=c["card"], foreground=c["text"])
        self.style.configure("Muted.TLabel", font=("Segoe UI", 10), background=c["card"], foreground=c["muted"])

    def configure_widget(self, widget, widget_type):
        """Apply theme to a specific widget based on its type."""
        c = self.colors

        if widget_type == "frame":
            widget.configure(bg=c["card"])
        elif widget_type == "label_title":
            widget.configure(bg=c["card"], fg=c["text"])
        elif widget_type == "label_muted":
            widget.configure(bg=c["card"], fg=c["muted"])
        elif widget_type == "text":
            widget.configure(bg=c["card"], fg=c["text"], insertbackground=c["text"])
        elif widget_type == "button_primary":
            widget.configure(bg=c["accent"], fg="white", activebackground=c["accent"], activeforeground="white",
                             cursor="hand2")
        elif widget_type == "button_danger":
            widget.configure(bg=c["card"], fg=c["danger"], activebackground=c["card"], activeforeground=c["danger"],
                             cursor="hand2")
        elif widget_type == "border_box":
            widget.configure(bg=c["card"], highlightbackground=c["border"])
        elif widget_type == "canvas":
            widget.configure(bg=c["bg"])
