"""
Application state manager for PANDA SCAN.
Handles all application state and workflow logic.
"""


class AppState:
    """Manages application state and workflow."""

    def __init__(self):
        self.current_file = None
        self.server_ok = False
        self.upload_ok = False
        self.is_busy = False
        self.status_state = "IDLE"

    def set_file(self, filepath):
        """Set the current file and reset upload status."""
        self.current_file = filepath
        self.upload_ok = False

    def clear_file(self):
        """Clear the current file."""
        self.current_file = None

    def set_server_status(self, ok):
        """Update server connection status."""
        self.server_ok = ok

    def set_upload_status(self, ok):
        """Update upload completion status."""
        self.upload_ok = ok

    def set_busy(self, busy):
        """Set busy state."""
        self.is_busy = busy

    def set_status(self, state):
        """Update status state."""
        self.status_state = state.upper()

    def reset(self):
        """Reset all state to initial values."""
        self.current_file = None
        self.server_ok = False
        self.upload_ok = False
        self.is_busy = False
        self.status_state = "IDLE"

    def can_upload(self):
        """Check if upload is allowed."""
        return bool(self.current_file) and self.server_ok and not self.is_busy

    def can_run(self):
        """Check if detection run is allowed."""
        return self.upload_ok and not self.is_busy

    def can_interact(self):
        """Check if user can interact with controls."""
        return not self.is_busy

    def get_zip_path(self):
        return self.current_file

