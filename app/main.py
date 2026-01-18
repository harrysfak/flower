"""
PANDA SCAN - Smart Image Detection Tool
Entry point for the application.
"""
import tkinter as tk
from app.tk_app.core.utils import make_dpi_aware_windows
from tk_app.app import PandaScanApp


def main():
    """Initialize and run the application."""
    make_dpi_aware_windows()

    root = tk.Tk()
    app = PandaScanApp(root)
    app.run()


if __name__ == "__main__":
    main()