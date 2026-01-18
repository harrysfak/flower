"""
Header UI components for PANDA SCAN.
Contains logo, title, and controls.
"""
import os
import tkinter as tk
from tkinter import ttk
from app.tk_app.core.config import APP_TITLE, LOGO_PATH
from app.tk_app.ui.widgets import StatusPill

try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except Exception:
    HAS_PIL = False


class Header:
    """Manages the header section."""

    def __init__(self, parent, on_theme_toggle):
        self.frame = ttk.Frame(parent)
        self.frame.grid_columnconfigure(1, weight=1)
        self.on_theme_toggle = on_theme_toggle

        self._logo_img = None
        self._build_ui()

    def _build_ui(self):
        """Build header UI components."""
        # Logo box
        self.logo_box = tk.Frame(self.frame, width=200, height=200, bd=0, highlightthickness=7)
        self.logo_box.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="w")
        self.logo_box.grid_propagate(False)

        self.logo_label = tk.Label(self.logo_box, text="")
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")
        self._load_logo()

        # Title and tagline
        self.title_label = ttk.Label(self.frame, text=APP_TITLE)
        self.title_label.grid(row=0, column=1, sticky="w", pady=(18, 0))

        # Right controls
        self.controls_frame = ttk.Frame(self.frame)
        self.controls_frame.grid(row=0, column=2, rowspan=2, padx=16, pady=16, sticky="e")

        self.var_dark = tk.IntVar(value=0)
        self.dark_toggle = ttk.Checkbutton(
            self.controls_frame,
            text="DARK",
            variable=self.var_dark,
            command=self.on_theme_toggle
        )
        self.dark_toggle.pack(side="right", padx=(10, 0))

        # Status pill
        self.status_pill = StatusPill(self.controls_frame)
        self.status_pill.pack(side="right")

    def _load_logo(self):
        """Load and display the panda logo."""
        if os.path.exists(LOGO_PATH) and HAS_PIL:
            try:
                img = Image.open(LOGO_PATH).convert("RGBA")
                img = img.resize((180, 180), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                self.logo_label.configure(image=self._logo_img, text="")
                print("OK")
                return
            except Exception:
                print("Not ok")
                pass
        self.logo_label.configure(text="🐼")

    def grid(self, **kwargs):
        """Grid the header."""
        self.frame.grid(**kwargs)

    def apply_theme(self, theme_manager):
        """Apply theme to header components."""
        c = theme_manager.colors

        self.frame.configure(style="Card.TFrame")
        self.controls_frame.configure(style="Card.TFrame")

        theme_manager.configure_widget(self.logo_box, "border_box")
        self.logo_label.configure(bg=c["card"], fg=c["text"])

        self.title_label.configure(style="Title.TLabel")

        self.status_pill.configure(bg=c["card"])

    def update_status_pill(self, status_text, theme_manager):
        """Update the status pill display."""
        self.status_pill.draw(status_text, theme_manager.colors, theme_manager.colors["border"])
