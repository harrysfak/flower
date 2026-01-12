import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import ctypes

import requests
import time
from urllib.parse import urlparse, urlunparse

from modules.config_loader import ConfigLoader
from modules.conxCheck import ConnectionChecker
from modules.detector import Detector
from modules.file_sender import FileSender


def make_dpi_aware():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # fallback (system DPI aware)
        except Exception:
            pass


make_dpi_aware()





class GuiModel:

    def __init__(self, root):
        self.root = root
        # main window config
        self.root.title("Welcome to our Model")
        self.root.geometry("900x900")
        self._setup_ui()
        self._setup_classes()   # <-- Connector after ui





    def _setup_ui(self):

        # Data input with {file_name_var}
        import_data_lbl = tk.Label(self.root, text="🗃️ Data input")
        import_data_lbl.grid(column=0, row=0, padx=40, pady=40)

        # function for search zip file
        import_data_btn = tk.Button(self.root, text="🔍 Search Data", command=self.browse_file)
        import_data_btn.grid(column=1, row=0, padx=40, pady=40)

        #Checking label for connection status
        self.status_lbl = tk.Label(self.root, text="No-Connection-Press BTN", font=("Arial", 14,))
        self.status_lbl.grid(column=1, row=1, padx=40, pady=40)

        self.requests_btn = tk.Button(self.root, text="🔍 Requests Check", command=self._wire_connection_events)
        self.requests_btn.grid(column=0, row=1, padx=40, pady=20)

        #run model predictions on files at unzipped dir
        self.run_lbl = tk.Label(self.root, text="Run Detection ➡️ ")
        self.run_lbl.grid(column=0, row=2, padx=40, pady=20)

        run_btn =  tk.Button(self.root, text="RUN", command=self.run_detect)
        run_btn.grid(column=1, row=2, padx=40, pady=20)

        self.unzip_status_lbl = tk.Label(self.root, text="Unzip progress: idle")
        self.unzip_status_lbl.grid(column=0, row=3, padx=40, pady=10)
        self.unzip_progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.unzip_progress.grid(column=1, row=3, padx=40, pady=10)

        self.detect_status_lbl = tk.Label(self.root, text="Detect progress: idle")
        self.detect_status_lbl.grid(column=0, row=4, padx=40, pady=10)
        self.detect_progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.detect_progress.grid(column=1, row=4, padx=40, pady=10)

    def _setup_classes(self):
        self.url = ConfigLoader("UPLOAD_URL_TESTING").load_value()
        self.detect_url = self._replace_path(self.url, "/detect")
        self.unzip_progress_url = self._replace_path(self.url, "/progress/unzip")
        self.detect_progress_url = self._replace_path(self.url, "/progress/detect")
        self.connector = ConnectionChecker(self.root, self.status_lbl, self.requests_btn)

    def _wire_connection_events(self):
        self.requests_btn.config(command=self.connector.requests_check_click)

    def _replace_path(self, url, new_path):
        parts = urlparse(url)
        return urlunparse(parts._replace(path=new_path))

    def _update_progress_ui(self, bar, label, data, title):
        percent = data.get("percent", 0)
        status = data.get("status", "idle")
        detail = data.get("detail", "")
        bar["value"] = percent
        label.config(text=f"{title}: {percent}% ({status}) {detail}".strip())

    def _poll_progress(self, url, bar, label, title):
        while True:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    self.root.after(0, lambda d=data: self._update_progress_ui(bar, label, d, title))
                    if data.get("status") in {"done", "error"}:
                        break
                else:
                    self.root.after(0, lambda: label.config(text=f"{title}: server error {resp.status_code}"))
                    break
            except Exception as e:
                self.root.after(0, lambda: label.config(text=f"{title}: {e}"))
                break
            time.sleep(0.5)


    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Επιλογή Αρχείου",
            filetypes=[("Zip Files", "*.zip"), ("All files", "*.*")])
        if not path:
            return

        self.filepath = path
        self.filename = os.path.basename(path)
        print("SENDING:", self.filepath)
        print("EXISTS:", os.path.exists(self.filepath))
        self.sender = FileSender(self.url, os.path.abspath(self.filepath))
        messagebox.showinfo("Επιτυχία", f"Φορτώθηκε: {self.filename}")
        import_data_lbl = tk.Label(self.root, text=self.filename, font="Bolt")
        import_data_lbl.grid(column=0, row=0, padx=40, pady=40)

        upload_btn = tk.Button(self.root, text="Upload zip file to FastAPI Server.\n(Check first if the server is running)", command=self._upload_file)
        upload_btn.grid(column=2, row=1, padx=40, pady=40)

        return self.filename

    import threading
    #Εκκινηση thread για το upload
    def _upload_file(self):
        self.status_lbl.config(text="⬆️ Uploading...")
        self.unzip_progress["value"] = 0
        self.unzip_status_lbl.config(text="Unzip progress: starting...")
        threading.Thread(target=self._poll_progress, args=(self.unzip_progress_url, self.unzip_progress, self.unzip_status_lbl, "Unzip progress"), daemon=True).start()
        threading.Thread(target=self._upload_worker, daemon=True).start()

    def _upload_worker(self):
        success, msg = self.sender.send_file()
        self.root.after(0, lambda: self._upload_done(success, msg))

    def _upload_done(self, success, msg):
        if success:
            self.status_lbl.config(text="✅ Upload OK")
            messagebox.showinfo("Επιτυχία", msg)
        else:
            self.status_lbl.config(text="❌ Upload failed")
            messagebox.showerror("Σφάλμα", msg)

    #Εκκινηση thread για το detect-predict
    def run_detect(self):
        self.run_lbl.config(text="🧠 Running detection...")
        self.detect_progress["value"] = 0
        self.detect_status_lbl.config(text="Detect progress: starting...")
        threading.Thread(target=self._poll_progress, args=(self.detect_progress_url, self.detect_progress, self.detect_status_lbl, "Detect progress"), daemon=True).start()
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        ok, result = Detector(url=self.detect_url).run()
        self.root.after(0, lambda: self._detect_done(ok, result))

    def _detect_done(self, ok, result):
        if ok:
            self.status_lbl.config(text="✅ Detect completed")
            messagebox.showinfo(
                "Detect OK",
                f"Αποθηκεύτηκε: {result['saved_txt']}, {os.path.abspath(result)}"
            )
        else:
            self.status_lbl.config(text="❌ Detect failed")
            messagebox.showerror("Error", result)


def run_gui():
    root = tk.Tk()

    app = GuiModel(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
