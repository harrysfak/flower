"""
Action handlers for PANDA SCAN application.
Contains all workflow action logic.
"""
import time
import threading
from tkinter import filedialog, messagebox
from pathlib import Path


class ActionHandler:
    """Handles all user actions and background tasks."""

    def __init__(self, app_state, logger, update_callback, api_client):
        self.state = app_state
        self.logger = logger
        self.update_ui = update_callback  # ΠΡΕΠΕΙ να κάνει root.after(0, fn)
        self.api = api_client

        """
        Initialize action handler.

        Args:
            app_state: AppState instance
            logger: LogManager instance
            update_callback: Callable to trigger UI updates
        """

    def _run_background(self, start_msg, work_fn, done_fn):
        """
        Execute a task in background with proper state management.

        Args:
            start_msg: Message to log when starting
            work_fn: Function that does the work, returns (ok, payload)
            done_fn: Function called when done with (ok, payload)
        """
        if self.state.is_busy:
            return

        self.state.set_busy(True)
        self.state.set_status("WORKING")
        self.update_ui()
        self.logger.log(start_msg, "info")

        def runner():
            try:
                ok, payload = work_fn()
            except Exception as e:
                ok, payload = False, str(e)

            def finish():
                self.state.set_busy(False)
                done_fn(ok, payload)
                self.update_ui()

            # Schedule UI update on main thread
            self.update_ui(finish)

        threading.Thread(target=runner, daemon=True).start()

    # --- Action Handlers ---

    def check_server(self):
        def work():
            return self.api.check_server()

        def done(ok, payload):
            self.state.set_server_status(bool(ok))
            self.state.set_status("OK" if ok else "ERROR")
            self.logger.log(str(payload), "ok" if ok else "err")

        self._run_background("Connection request to inference engine…", work, done)

    def browse_file(self):
        """Browse for ZIP file."""
        if self.state.is_busy:
            return

        path = filedialog.askopenfilename(
            title="Select ZIP dataset",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )

        if not path:
            return

        self.state.set_file(path)
        self.state.set_status("IDLE")
        self.logger.log(f"ZIP selected: {Path(path).name}", "ok")
        self.update_ui()

    def upload_dataset(self):
        zip_path = self.state.current_file  # <-- σωστό πεδίο από AppState
        if not zip_path:
            messagebox.showerror("Missing ZIP", "Select a ZIP first.")
            return

        # προαιρετικό: αν θες να επιβάλλεις και server check πριν upload
        if not self.state.server_ok:
            messagebox.showerror("No connection", "Check server first.")
            return

        def work():
            ok, payload = self.api.upload_zip(zip_path)
            # αν το API γυρνά dataset_id, το κρατάμε
            if ok and isinstance(payload, dict) and payload.get("dataset_id"):
                setattr(self.state, "dataset_id", payload["dataset_id"])
            return ok, payload

        def done(ok, payload):
            self.state.set_upload_status(bool(ok))
            self.state.set_status("OK" if ok else "ERROR")
            self.logger.log(str(payload), "ok" if ok else "err")

        self._run_background("Uploading dataset…", work, done)

    def run_detection(self):
        def work():
            dataset_id = getattr(self.state, "dataset_id", None)
            ok, payload = self.api.run_detection(dataset_id=dataset_id)
            if ok and isinstance(payload, dict) and payload.get("job_id"):
                setattr(self.state, "job_id", payload["job_id"])
            return ok, payload

        def done(ok, payload):
            self.state.set_status("DONE" if ok else "ERROR")
            self.logger.log(str(payload), "ok" if ok else "err")

        self._run_background("Starting detection…", work, done)

    def download_results(self):
        if self.state.is_busy:
            return

        save_path = filedialog.asksaveasfilename(
            title="Save results CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not save_path:
            return

        def work():
            job_id = getattr(self.state, "job_id", None)
            return self.api.download_csv(save_to=save_path, job_id=job_id)

        def done(ok, payload):
            self.state.set_status("OK" if ok else "ERROR")
            self.logger.log(f"CSV saved: {payload}" if ok else str(payload), "ok" if ok else "err")

        self._run_background("Downloading results…", work, done)

    def reset_workspace(self):
        if self.state.is_busy:
            return
        if not messagebox.askyesno("Reset Workspace", "This will clear server temp files.\nContinue?"):
            return

        def work():
            # αν θες μόνο το τρέχον dataset:
            # return self.api.reset_server(getattr(self.state, "dataset_id", None))
            return self.api.reset_server()

        def done(ok, payload):
            if ok:
                self.state.reset()
                self.logger.log(str(payload), "ok")
            else:
                self.state.set_status("ERROR")
                self.logger.log(str(payload), "err")

        self._run_background("Resetting server workspace…", work, done)
