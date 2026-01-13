import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import ctypes

import requests

from modules.config_loader import ConfigLoader
from modules.conxCheck import ConnectionChecker
from modules.detector import ApiCaller
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
        import_data_lbl = tk.Label(self.root, text="🗃️ Data input", font=("Arial", 14,))
        import_data_lbl.grid(column=0, row=1, padx=40, pady=40)

        # function for search zip file
        import_data_btn = tk.Button(self.root, text="🔍 Search Data", command=self.browse_file)
        import_data_btn.grid(column=1, row=1, padx=40, pady=40)

        #Checking label for connection status
        self.status_lbl = tk.Label(self.root, text="No-Connection-Press CHECK", font=("Arial", 14,))
        self.status_lbl.grid(column=0, row=0, padx=40, pady=40,)

        self.requests_lbl = tk.Label(self.root, text="Check if server is connected ➡️", font=("Arial", 14,))
        self.requests_lbl.grid(column=0, row=2, padx=40, pady=20)

        self.requests_btn = tk.Button(self.root, text="🔍 CHECK", command=self._wire_connection_events)
        self.requests_btn.grid(column=1, row=2, padx=40, pady=20)

        #run model predictions on files at unzipped dir
        self.run_lbl = tk.Label(self.root, text="Run Detection ➡️ ", font=("Arial", 14,))
        self.run_lbl.grid(column=0, row=3, padx=40, pady=20)

        run_btn = tk.Button(self.root, text="RUN", command=self.run_detect)
        run_btn.grid(column=1, row=3, padx=40, pady=20)

        download_lbl = tk.Label(self.root, text="Click to download results csv ➡️", font=("Arial", 14,))
        download_lbl.grid(column=0, row=4, padx=40, pady=20)

        download_btn = tk.Button(self.root, text="Download", command=self.download)
        download_btn.grid(column=1, row=4, padx=40, pady=20)


    def _setup_classes(self):
        self.api = ApiCaller()
        self.url = ConfigLoader("UPLOAD_URL_TESTING").load_value()
        self.connector = ConnectionChecker(self.root, self.status_lbl, self.requests_btn)

    def _wire_connection_events(self):
        self.requests_btn.config(command=self.connector.requests_check_click)


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

        upload_btn = tk.Button(self.root, text="Upload zip file to Flask Server.\n(Check first if the server is running)", command=self._upload_file)
        upload_btn.grid(column=2, row=1, padx=40, pady=40)

        return self.filename

    import threading
    #Εκκινηση thread για το upload
    def _upload_file(self):
        self.status_lbl.config(text="⬆️ Uploading...")
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
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        ok, result = self.api.run()
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
    def download(self):
        ok, saved = self.api.download()
        if ok:
            print("✅ CSV downloaded at:", saved)
        else:
            print("❌ Download failed:", saved)


def run_gui():
    root = tk.Tk()

    app = GuiModel(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
