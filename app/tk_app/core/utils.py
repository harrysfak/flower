"""
Utility functions for PANDA SCAN application.
"""
import ctypes
import sys


def make_dpi_aware_windows():
    """Make the application DPI-aware on Windows."""
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def round_rect_points(x1, y1, x2, y2, r):
    """Generate points for a rounded rectangle path."""
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
    ]
