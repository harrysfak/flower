"""
Logger component for PANDA SCAN application.
Manages the diagnostic log display.
"""
import time
import tkinter as tk


class LogManager:
    """Manages the diagnostic log widget."""

    def __init__(self, text_widget):
        self.text_widget = text_widget
        self._configure_tags()

    def _configure_tags(self):
        """Configure text tags for different log types."""
        self.text_widget.tag_configure("ok", foreground="#16A34A")
        self.text_widget.tag_configure("err", foreground="#E14B4B")
        self.text_widget.tag_configure("info", foreground="#6B7280")

    def log(self, msg, kind="info"):
        """Add a log entry with timestamp and appropriate styling."""
        ts = time.strftime("[%H:%M:%S]")

        if kind == "info":
            prefix = "→"
        elif kind == "ok":
            prefix = "✓"
        else:  # err
            prefix = "×"

        line = f"{ts} {prefix} {msg}\n"
        self.text_widget.insert("end", line, kind)
        self.text_widget.see("end")

    def clear(self):
        """Clear all log entries."""
        self.text_widget.delete("1.0", "end")
