"""
ConnectorChecker
"""
import subprocess
import sys
import threading

import requests


class ConnectionChecker:
    def __init__(self, root, label, btn):
        self.root = root
        self.status_lbl = label
        self.requests_btn = btn

    def requests_check_click(self):
        self.status_lbl.config(text="🔄 Ελέγχεται...")
        self.requests_btn.config(state="disabled")

        thread = threading.Thread(target=self._requests_check_worker, daemon=True)
        thread.start()

    def _requests_check_worker(self, port=5000):
        try:
            url = f'http://localhost:{port}/health'
            resp = requests.get(url, timeout=5)
            status = f"✅ Connected ({resp.status_code})" if resp.status_code == 200 else f"⚠️ {resp.status_code}"
        except requests.exceptions.ConnectionError:
            status = "❌ Connection Denied"

        except requests.exceptions.Timeout:
            status = "⏰ Timeout"
        except:
            status = "❌ Error"

        self.root.after(0, lambda: self._update_status(status))

    def _update_status(self, status):
        self.status_lbl.config(text=status)
        self.requests_btn.config(state="normal")
