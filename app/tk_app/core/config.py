"""
Configuration module for PANDA SCAN application.
Contains all constants, colors, and settings.
"""
import os.path

APP_TITLE = "PANDA SCAN"

VERSION_TEXT = "VERSION 1.0.4 • OFFLINE"

LOGO_PATH = r"C:\Users\mpamp\Υπολογιστής\code\flower\flower\app\tk_app\assets\panda.png"


# Window settings
WINDOW_GEOMETRY = "1200x780"
WINDOW_MIN_SIZE = (980, 640)

# Left panel width
LEFT_PANEL_WIDTH = 330

# Color schemes
LIGHT = {
    "bg": "#F6F3EE",
    "card": "#FFFFFF",
    "text": "#1F2328",
    "muted": "#6B7280",
    "border": "#E7E3DC",
    "pill": "#F2F2F2",
    "accent": "#F08A5D",
    "danger": "#E14B4B",
}

DARK = {
    "bg": "#0F1115",
    "card": "#151923",
    "text": "#EAECEF",
    "muted": "#A1A1AA",
    "border": "#262B36",
    "pill": "#1E2230",
    "accent": "#F08A5D",
    "danger": "#E14B4B",
}

# Status pill colors by state
STATUS_PILL_COLORS = {
    "IDLE": {"light": "#F2F2F2", "dark": "#1E2230"},
    "WORKING": {"light": "#F6C177", "dark": "#3B2E1E"},
    "RUNNING": {"light": "#F6C177", "dark": "#3B2E1E"},
    "OK": {"light": "#B7E4C7", "dark": "#1B3A2A"},
    "DONE": {"light": "#B7E4C7", "dark": "#1B3A2A"},
    "ERROR": {"light": "#FECACA", "dark": "#3A1D1D"},
    "FAILED": {"light": "#FECACA", "dark": "#3A1D1D"},
}

