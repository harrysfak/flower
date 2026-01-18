# managers/api_client.py
from dataclasses import dataclass
from pathlib import Path
import requests
import os, re

@dataclass
class ApiConfig:
    base_url: str = "http://127.0.0.1:5000"
    timeout_short: float = 5.0
    timeout_upload: float = 30.0
    timeout_detect: float = 120.0

class ApiClient:
    def __init__(self, cfg: ApiConfig):
        self.cfg = cfg
        self.base = cfg.base_url.rstrip("/")
        self.s = requests.Session()

    def check_server(self):
        try:
            r = self.s.get(f"{self.base}/health", timeout=self.cfg.timeout_short)
            return (r.status_code == 200), f"Connected ({r.status_code})" if r.ok else f"HTTP {r.status_code}"
        except requests.exceptions.Timeout: return False, "Timeout"
        except requests.exceptions.ConnectionError: return False, "Connection Denied"
        except Exception as e: return False, str(e)

    def upload_zip(self, zip_path: str):
        p = Path(zip_path)
        if not p.exists(): return False, "ZIP not found"
        try:
            with p.open("rb") as f:
                files = {"the_file": (p.name, f, "application/zip")}  # ίδιο field με FileSender
                r = self.s.post(f"{self.base}/upload", files=files, timeout=self.cfg.timeout_upload)
            if not r.ok: return False, f"Upload failed ({r.status_code}): {r.text[:200]}"
            # αν ο server γυρνά dataset_id/JSON, το πιάνεις εδώ:
            try: return True, r.json()
            except: return True, r.text
        except Exception as e:
            return False, str(e)

    def run_detection(self, dataset_id: str | None = None):
        try:
            r = self.s.post(f"{self.base}/detect", json=({"dataset_id": dataset_id} if dataset_id else None),
                            timeout=self.cfg.timeout_detect)
            if not r.ok: return False, f"Detect failed ({r.status_code}): {r.text[:200]}"
            try: return True, r.json()
            except: return True, r.text
        except Exception as e:
            return False, str(e)

    def download_csv(self, save_path: str):
        try:
            r = self.s.get(f"{self.base}/download", stream=True, timeout=self.cfg.timeout_detect)
            if not r.ok: return False, f"Download failed ({r.status_code}): {r.text[:200]}"
            Path(save_path).write_bytes(r.content)
            return True, save_path
        except Exception as e:
            return False, str(e)

    def reset_server(self):
        url = f"{self.base}/reset"
        try:
            r = self.s.post(url, timeout=self.cfg.timeout_short)
            if not r.ok:
                return False, f"Reset failed ({r.status_code}): {r.text[:200]}"
            return True, r.json()
        except Exception as e:
            return False, str(e)
