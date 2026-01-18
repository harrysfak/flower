"""
Workflow card UI components for PANDA SCAN.
Contains all workflow steps and controls.
"""
import os
import tkinter as tk
from tkinter import ttk
from app.tk_app.core.config import VERSION_TEXT


class WorkflowCard:
    """Manages the main workflow card."""

    def __init__(self, parent, callbacks):
        """
        Initialize workflow card.

        Args:
            parent: Parent widget
            callbacks: Dict with keys: check, browse, upload, run, download, reset
        """
        self.callbacks = callbacks
        self.card = tk.Frame(parent, bd=0, highlightthickness=1)

        self._build_ui()

    def _build_ui(self):
        """Build all workflow UI components."""
        # Header
        header = tk.Frame(self.card, bd=0, highlightthickness=0)
        header.pack(fill="x", padx=18, pady=(18, 10))
        header.grid_columnconfigure(0, weight=1)

        # Left side: title and subtitle
        left = tk.Frame(header, bd=0, highlightthickness=0)
        left.grid(row=0, column=0, sticky="w")

        self.title = tk.Label(left, text="Analysis Workflow", font=("Segoe UI Semibold", 14))
        self.title.pack(anchor="w")

        self.subtitle = tk.Label(left, text="Follow the steps to process your dataset.", font=("Segoe UI", 11))
        self.subtitle.pack(anchor="w", pady=(4, 0))

        # Right side: current file box
        self.file_box = tk.Frame(header, bd=0, highlightthickness=1)
        self.file_box.grid(row=0, column=1, sticky="e", padx=(12, 0))

        self.file_title = tk.Label(self.file_box, text="CURRENT FILE", font=("Segoe UI Semibold", 9))
        self.file_value = tk.Label(self.file_box, text="No file selected", font=("Segoe UI", 11))
        self.file_title.pack(anchor="w", padx=12, pady=(10, 0))
        self.file_value.pack(anchor="w", padx=12, pady=(4, 10))

        # Steps
        self.step1_btn = self._create_step(
            "1. System Check",
            "Verify connection to the inference engine.",
            "Check Server",
            self.callbacks["check"]
        )

        self.step2_btn = self._create_step(
            "2. Select Dataset",
            "Choose a ZIP file containing images.",
            "Browse ZIP",
            self.callbacks["browse"]
        )

        self.step3_btn = self._create_step(
            "3. Upload to Cloud",
            "Securely transfer data for processing.",
            "Upload",
            self.callbacks["upload"]
        )

        # Run detection block
        self._create_run_block()

        # Results step
        self.step5_btn = self._create_step(
            "5. Results",
            "Download the generated CSV report.",
            "Download CSV",
            self.callbacks["download"]
        )

        # Footer
        self._create_footer()

    def _create_step(self, title, description, button_text, command):
        """Create a workflow step row."""
        row = tk.Frame(self.card, bd=0, highlightthickness=0)
        row.pack(fill="x", padx=18, pady=8)
        row.grid_columnconfigure(0, weight=1)

        # Left: text
        left = tk.Frame(row, bd=0, highlightthickness=0)
        left.grid(row=0, column=0, sticky="w")

        t = tk.Label(left, text=title, font=("Segoe UI Semibold", 12))
        d = tk.Label(left, text=description, font=("Segoe UI", 11))
        t.pack(anchor="w")
        d.pack(anchor="w", pady=(2, 0))

        # Right: button
        btn = ttk.Button(row, text=button_text, command=command)
        btn.grid(row=0, column=1, sticky="e")

        return btn

    def _create_run_block(self):
        """Create the primary run detection block."""
        run_block = tk.Frame(self.card, bd=0, highlightthickness=0)
        run_block.pack(fill="x", padx=18, pady=(8, 10))

        self.run_title = tk.Label(run_block, text="4. Run Detection", font=("Segoe UI Semibold", 14))
        self.run_desc = tk.Label(run_block, text="Start the AI analysis on the uploaded dataset.",
                                 font=("Segoe UI", 11))
        self.run_title.pack(anchor="center", pady=(12, 4))
        self.run_desc.pack(anchor="center", pady=(0, 12))

        self.btn_run = tk.Button(
            run_block,
            text="▶  RUN DETECTION",
            command=self.callbacks["run"],
            relief="flat",
            bd=0,
            padx=18,
            pady=10
        )
        self.btn_run.pack(anchor="center", pady=(0, 14))

    def _create_footer(self):
        """Create the footer with version and reset button."""
        footer = tk.Frame(self.card, bd=0, highlightthickness=0)
        footer.pack(fill="x", padx=18, pady=(6, 16))
        footer.grid_columnconfigure(0, weight=1)

        self.version_label = tk.Label(footer, text=VERSION_TEXT, font=("Segoe UI", 10))
        self.version_label.grid(row=0, column=0, sticky="w")

        self.btn_reset = tk.Button(
            footer,
            text="🗑  Reset Workspace",
            command=self.callbacks["reset"],
            relief="flat",
            bd=0,
            padx=12,
            pady=8
        )
        self.btn_reset.grid(row=0, column=1, sticky="e")

    def pack(self, **kwargs):
        """Pack the workflow card."""
        self.card.pack(**kwargs)

    def set_file_label(self, filepath):
        """Update the current file label."""
        text = os.path.basename(filepath) if filepath else "No file selected"
        self.file_value.configure(text=text)

    def update_buttons(self, state):
        """
        Update button states based on app state.

        Args:
            state: AppState instance
        """
        can_upload = state.can_upload()
        can_run = state.can_run()
        can_interact = state.can_interact()

        self.step1_btn.configure(state=("normal" if can_interact else "disabled"))
        self.step2_btn.configure(state=("normal" if can_interact else "disabled"))
        self.step3_btn.configure(state=("normal" if can_upload else "disabled"))
        self.btn_run.configure(state=("normal" if can_run else "disabled"))
        self.step5_btn.configure(state=("normal" if can_interact else "disabled"))
        self.btn_reset.configure(state=("normal" if can_interact else "disabled"))

    def apply_theme(self, theme_manager):
        """Apply theme to all workflow components."""
        c = theme_manager.colors

        theme_manager.configure_widget(self.card, "border_box")

        # Header
        theme_manager.configure_widget(self.title, "label_title")
        theme_manager.configure_widget(self.subtitle, "label_muted")

        # File box
        theme_manager.configure_widget(self.file_box, "border_box")
        theme_manager.configure_widget(self.file_title, "label_muted")
        theme_manager.configure_widget(self.file_value, "label_title")

        # Run block
        theme_manager.configure_widget(self.run_title, "label_title")
        theme_manager.configure_widget(self.run_desc, "label_muted")
        theme_manager.configure_widget(self.btn_run, "button_primary")

        # Footer
        theme_manager.configure_widget(self.version_label, "label_muted")
        theme_manager.configure_widget(self.btn_reset, "button_danger")

        # Apply to all step rows
        self._apply_theme_to_children(self.card, theme_manager)

    def _apply_theme_to_children(self, container, theme_manager):
        """Recursively apply theme to all child widgets."""
        c = theme_manager.colors

        for child in container.winfo_children():
            if isinstance(child, tk.Label):
                if "Semibold" in str(child.cget("font")):
                    theme_manager.configure_widget(child, "label_title")
                else:
                    theme_manager.configure_widget(child, "label_muted")
            elif isinstance(child, tk.Frame):
                theme_manager.configure_widget(child, "frame")
                self._apply_theme_to_children(child, theme_manager)
