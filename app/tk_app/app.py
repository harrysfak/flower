"""
Main application class for PANDA SCAN.
Orchestrates all components and UI.
"""
import tkinter as tk
from tkinter import ttk

from app.tk_app.core.config import WINDOW_GEOMETRY, WINDOW_MIN_SIZE
from app.tk_app.managers.api_client import ApiClient, ApiConfig
from app.tk_app.core.state import AppState
from app.tk_app.managers.logger import LogManager
from app.tk_app.managers.theme import ThemeManager
from app.tk_app.managers.actions import ActionHandler
from app.tk_app.ui.widgets import Scrollable
from app.tk_app.ui.ui_left_panel import LeftPanel
from app.tk_app.ui.ui_header import Header
from app.tk_app.ui.ui_workflow import WorkflowCard


class PandaScanApp:
    """Main application controller."""

    def __init__(self, root):
        self.root = root
        self.root.title("PANDA SCAN")
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.minsize(*WINDOW_MIN_SIZE)

        # Initialize core components
        self.state = AppState()
        self.style = ttk.Style()
        # 1) φτιάχνεις client
        cfg = ApiConfig(base_url="http://127.0.0.1:5000")
        self.api = ApiClient(cfg)
        self.theme = ThemeManager(self.root, self.style)

        # Build UI
        self._build_layout()

        # Initialize managers (after UI is built)
        self.logger = LogManager(self.left_panel.log_text)
        self.actions = ActionHandler(self.state, self.logger, self._schedule_ui_update, self.api)

        # Connect actions to workflow buttons
        self._connect_actions()

        # Initial setup
        self.theme.apply_to_root()
        self.theme.apply_to_ttk()
        self._apply_theme()
        self._update_status("IDLE")
        self._refresh_ui()

        self.logger.log("App ready.")

    def _build_layout(self):
        """Build the main application layout."""
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Left panel
        self.left_panel = LeftPanel(self.root)
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(20, 12), pady=20)

        # Right panel
        self.right_panel = ttk.Frame(self.root)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 20), pady=20)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        # Header
        self.header = Header(self.right_panel, self._on_theme_toggle)
        self.header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))

        # Scrollable body
        self.scroll_area = Scrollable(self.right_panel)
        self.scroll_area.grid(row=1, column=0, sticky="nsew", padx=18, pady=(12, 18))

        # Body wrapper
        self.body_wrapper = tk.Frame(self.scroll_area.inner, bd=0, highlightthickness=0)
        self.body_wrapper.pack(fill="both", expand=True, padx=16, pady=16)

        # Workflow card (with placeholder callbacks)
        callbacks = {
            "check": lambda: None,
            "browse": lambda: None,
            "upload": lambda: None,
            "run": lambda: None,
            "download": lambda: None,
            "reset": lambda: None,
        }
        self.workflow = WorkflowCard(self.body_wrapper, callbacks)
        self.workflow.pack(fill="x", expand=True)

    def _connect_actions(self):
        """Connect action handlers to workflow buttons after initialization."""
        self.workflow.step1_btn.configure(command=self.actions.check_server)
        self.workflow.step2_btn.configure(command=self.actions.browse_file)
        self.workflow.step3_btn.configure(command=self.actions.upload_dataset)
        self.workflow.btn_run.configure(command=self.actions.run_detection)
        self.workflow.step5_btn.configure(command=self.actions.download_results)
        self.workflow.btn_reset.configure(command=self.actions.reset_workspace)

    def _on_theme_toggle(self):
        """Handle theme toggle."""
        self.theme.toggle_theme()
        self.theme.apply_to_root()
        self.theme.apply_to_ttk()
        self._apply_theme()
        self._update_status(self.state.status_state)

    def _apply_theme(self):
        """Apply current theme to all components."""
        self.body_wrapper.configure(bg=self.theme.colors["bg"])

        self.left_panel.apply_theme(self.theme)
        self.header.apply_theme(self.theme)
        self.workflow.apply_theme(self.theme)

        self.theme.configure_widget(self.scroll_area.canvas, "canvas")
        self.scroll_area.inner.configure(style="Card.TFrame")

        # Update log text tags with current theme
        c = self.theme.colors
        self.left_panel.log_text.tag_configure("ok", foreground="#16A34A")
        self.left_panel.log_text.tag_configure("err", foreground=c["danger"])
        self.left_panel.log_text.tag_configure("info", foreground=c["muted"])

    def _update_status(self, status):
        """Update status display."""
        self.state.set_status(status)

        # Update pill color based on state
        pill_color = self.theme.get_pill_color(status)
        self.theme.colors["pill"] = pill_color

        self.header.update_status_pill(status, self.theme)

    def _refresh_ui(self):
        """Refresh all UI elements based on current state."""
        self.workflow.set_file_label(self.state.current_file)
        self.workflow.update_buttons(self.state)
        self._update_status(self.state.status_state)

    def _schedule_ui_update(self, callback=None):
        """
        Schedule a UI update on the main thread.

        Args:
            callback: Optional callback to execute before refresh
        """
        def update():
            if callback:
                callback()
            self._refresh_ui()

        self.root.after(0, update)

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()