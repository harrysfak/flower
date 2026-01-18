# PandaScan — CustomTkinter UI (Monochrome Pro)
# Requires:
#   pip install customtkinter pillow
#
# Notes:
# - Βάλε το logo σου (PNG) σε ένα path και δήλωσέ το στο LOGO_PATH.
# - Τα callbacks (check/upload/run/download/reset) είναι stubs για να συνδέσεις τα modules σου.

import os
import time
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

# ---------- CONFIG ----------
APP_TITLE = "PANDA SCAN"
TAGLINE = "SMART IMAGE DETECTION • CLEAN & QUIET"
VERSION_TEXT = "VERSION 1.0.4 • OFFLINE"

# Βάλε εδώ το logo σου (panda mark). Π.χ. "assets/panda_logo.png"
LOGO_PATH = "../../panda.png"  # <-- άλλαξέ το στο δικό σου

# Monochrome palette (accent only for primary CTA)
ACCENT = "#F08A5D"        # soft orange (primary button)
DANGER = "#E14B4B"        # danger red
BG_LIGHT = "#F6F3EE"      # off-white
CARD_LIGHT = "#FFFFFF"
TEXT_DARK = "#1F2328"
MUTED = "#6B7280"
BORDER = "#E7E3DC"

BG_DARK = "#0F1115"
CARD_DARK = "#151923"
TEXT_LIGHT = "#EAECEF"
MUTED_DARK = "#A1A1AA"
BORDER_DARK = "#262B36"


class PandaScanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # window
        self.title(APP_TITLE)
        self.geometry("1200x780")
        self.minsize(980, 640)

        # ctk global
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")  # we override colors via fg_color mostly

        # state
        self.current_file = None
        self.server_ok = False
        self.upload_ok = False
        self.is_busy = False

        # build UI
        self._build_layout()
        self._apply_theme("light")
        self._set_status("IDLE")
        self._refresh_buttons()
        self._log("App ready.")

    # ---------------- LAYOUT ----------------
    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)  # left diagnostics
        self.grid_columnconfigure(1, weight=1)  # main
        self.grid_rowconfigure(0, weight=1)

        # LEFT: Diagnostics panel
        self.left_panel = ctk.CTkFrame(self, corner_radius=18)
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(20, 12), pady=20)
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.configure(width=330)

        left_title_row = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        left_title_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        left_title_row.grid_columnconfigure(0, weight=1)

        self.diag_title = ctk.CTkLabel(left_title_row, text="SYSTEM DIAGNOSTICS", font=ctk.CTkFont(size=12, weight="bold"))
        self.diag_title.grid(row=0, column=0, sticky="w")

        # small status dots (cosmetic)
        dots = ctk.CTkFrame(left_title_row, fg_color="transparent")
        dots.grid(row=0, column=1, sticky="e")
        self.dot1 = ctk.CTkLabel(dots, text="●", font=ctk.CTkFont(size=14))
        self.dot2 = ctk.CTkLabel(dots, text="●", font=ctk.CTkFont(size=14))
        self.dot1.pack(side="left", padx=(0, 6))
        self.dot2.pack(side="left")

        self.log_box = ctk.CTkTextbox(self.left_panel, corner_radius=16, border_width=1, wrap="word")
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # MAIN: container
        self.main = ctk.CTkFrame(self, corner_radius=18)
        self.main.grid(row=0, column=1, sticky="nsew", padx=(12, 20), pady=20)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        # HEADER
        self.header = ctk.CTkFrame(self.main, corner_radius=18)
        self.header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        self.header.grid_columnconfigure(1, weight=1)

        # Logo square
        self.logo_wrap = ctk.CTkFrame(self.header, corner_radius=16, width=56, height=56)
        self.logo_wrap.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="w")
        self.logo_wrap.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(self.logo_wrap, text="")
        self.logo_label.place(relx=0.5, rely=0.5, anchor="center")
        self._load_logo()

        # Title + tagline
        self.title_label = ctk.CTkLabel(self.header, text=APP_TITLE, font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=1, sticky="w", pady=(18, 0))

        self.tagline_label = ctk.CTkLabel(self.header, text=TAGLINE, font=ctk.CTkFont(size=12))
        self.tagline_label.grid(row=1, column=1, sticky="w", pady=(0, 18))

        # Status pill + theme toggle on the right
        right_controls = ctk.CTkFrame(self.header, fg_color="transparent")
        right_controls.grid(row=0, column=2, rowspan=2, padx=16, pady=16, sticky="e")

        self.theme_switch = ctk.CTkSwitch(
            right_controls, text="DARK", command=self._on_toggle_theme
        )
        self.theme_switch.pack(side="right", padx=(10, 0))

        self.status_pill = ctk.CTkFrame(right_controls, corner_radius=999, border_width=1)
        self.status_pill.pack(side="right")

        self.status_text = ctk.CTkLabel(self.status_pill, text="IDLE", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_text.pack(padx=14, pady=8)

        # BODY content
        self.body = ctk.CTkFrame(self.main, corner_radius=18)
        self.body.grid(row=1, column=0, sticky="nsew", padx=18, pady=(12, 12))
        self.body.grid_columnconfigure(0, weight=1)

        # Workflow card
        self.workflow = ctk.CTkFrame(self.body, corner_radius=18, border_width=1)
        self.workflow.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self.workflow.grid_columnconfigure(0, weight=1)
        self.workflow.grid_columnconfigure(1, weight=0)

        # Workflow header row
        wf_header = ctk.CTkFrame(self.workflow, fg_color="transparent")
        wf_header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 8))
        wf_header.grid_columnconfigure(0, weight=1)
        wf_header.grid_columnconfigure(1, weight=0)

        self.wf_title = ctk.CTkLabel(wf_header, text="Analysis Workflow", font=ctk.CTkFont(size=16, weight="bold"))
        self.wf_title.grid(row=0, column=0, sticky="w")

        self.wf_sub = ctk.CTkLabel(wf_header, text="Follow the steps to process your dataset.", font=ctk.CTkFont(size=12))
        self.wf_sub.grid(row=1, column=0, sticky="w", pady=(4, 0))

        file_box = ctk.CTkFrame(wf_header, corner_radius=14, border_width=1)
        file_box.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))
        file_box.grid_columnconfigure(0, weight=1)

        self.file_title = ctk.CTkLabel(file_box, text="CURRENT FILE", font=ctk.CTkFont(size=10, weight="bold"))
        self.file_title.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self.file_value = ctk.CTkLabel(file_box, text="No file selected", font=ctk.CTkFont(size=12))
        self.file_value.grid(row=1, column=0, sticky="w", padx=12, pady=(4, 10))

        # Steps
        self._step_row(1, "1. System Check", "Verify connection to the inference engine.", "Check Server", self.on_check_server)
        self._step_row(2, "2. Select Dataset", "Choose a ZIP file containing images.", "Browse ZIP", self.on_browse_zip)
        self._step_row(3, "3. Upload to Cloud", "Securely transfer data for processing.", "Upload", self.on_upload, disabled=True)

        # Run detection block (centered CTA)
        run_block = ctk.CTkFrame(self.workflow, corner_radius=18, border_width=0)
        run_block.grid(row=4, column=0, columnspan=2, sticky="ew", padx=18, pady=(10, 12))
        run_block.grid_columnconfigure(0, weight=1)

        self.run_title = ctk.CTkLabel(run_block, text="4. Run Detection", font=ctk.CTkFont(size=16, weight="bold"))
        self.run_title.grid(row=0, column=0, sticky="n", pady=(12, 4))

        self.run_desc = ctk.CTkLabel(run_block, text="Start the AI analysis on the uploaded dataset.", font=ctk.CTkFont(size=12))
        self.run_desc.grid(row=1, column=0, sticky="n", pady=(0, 12))

        self.btn_run = ctk.CTkButton(
            run_block, text="▶  RUN DETECTION", height=44, corner_radius=12,
            command=self.on_run_detection
        )
        self.btn_run.grid(row=2, column=0, pady=(0, 14))

        # Results row
        self._step_row(5, "5. Results", "Download the generated CSV report.", "Download CSV", self.on_download)

        # Footer row inside workflow
        footer = ctk.CTkFrame(self.workflow, fg_color="transparent")
        footer.grid(row=6, column=0, columnspan=2, sticky="ew", padx=18, pady=(4, 16))
        footer.grid_columnconfigure(0, weight=1)

        self.footer_left = ctk.CTkLabel(footer, text=VERSION_TEXT, font=ctk.CTkFont(size=11))
        self.footer_left.grid(row=0, column=0, sticky="w")

        self.btn_reset = ctk.CTkButton(
            footer, text="🗑  Reset Workspace", fg_color="transparent",
            border_width=1, corner_radius=12, command=self.on_reset,
        )
        self.btn_reset.grid(row=0, column=1, sticky="e")

    def _step_row(self, row_index, title, desc, btn_text, cmd, disabled=False):
        row = ctk.CTkFrame(self.workflow, fg_color="transparent")
        row.grid(row=row_index, column=0, columnspan=2, sticky="ew", padx=18, pady=8)
        row.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        t = ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=13, weight="bold"))
        t.pack(anchor="w")
        d = ctk.CTkLabel(left, text=desc, font=ctk.CTkFont(size=12))
        d.pack(anchor="w", pady=(2, 0))

        btn = ctk.CTkButton(row, text=btn_text, width=140, height=34, corner_radius=10, command=cmd)
        btn.grid(row=0, column=1, sticky="e")
        if disabled:
            btn.configure(state="disabled")

        # store some buttons we care about
        if "Upload" in btn_text:
            self.btn_upload = btn
        if "Download" in btn_text:
            self.btn_download = btn
        if "Check" in btn_text:
            self.btn_check = btn
        if "Browse" in btn_text:
            self.btn_browse = btn

    # ---------------- THEME ----------------
    def _apply_theme(self, mode: str):
        # mode: "light" or "dark"
        self._mode = mode

        if mode == "light":
            self.configure(fg_color=BG_LIGHT)
            self.left_panel.configure(fg_color=CARD_LIGHT, border_width=1, border_color=BORDER)
            self.main.configure(fg_color=CARD_LIGHT, border_width=1, border_color=BORDER)
            self.header.configure(fg_color=CARD_LIGHT, border_width=1, border_color=BORDER)
            self.body.configure(fg_color=CARD_LIGHT, border_width=0)
            self.workflow.configure(fg_color=CARD_LIGHT, border_width=1, border_color=BORDER)

            # text
            for w in [self.diag_title, self.title_label, self.wf_title, self.run_title]:
                w.configure(text_color=TEXT_DARK)
            for w in [self.tagline_label, self.wf_sub, self.run_desc, self.footer_left]:
                w.configure(text_color=MUTED)

            # log
            self.log_box.configure(fg_color=CARD_LIGHT, text_color=TEXT_DARK, border_color=BORDER)

            # pills / accents
            self.status_pill.configure(fg_color="#F2F2F2", border_color=BORDER)
            self.status_text.configure(text_color=TEXT_DARK)

            # logo wrap
            self.logo_wrap.configure(fg_color=CARD_LIGHT, border_width=1, border_color=BORDER)

            # buttons
            self.btn_run.configure(fg_color=ACCENT, hover_color="#F39C7A", text_color="white")
            self.btn_reset.configure(text_color=DANGER, border_color=BORDER, hover_color="#F7F7F7")

            # dots
            self.dot1.configure(text_color="#9CA3AF")
            self.dot2.configure(text_color="#22C55E")

        else:
            self.configure(fg_color=BG_DARK)
            self.left_panel.configure(fg_color=CARD_DARK, border_width=1, border_color=BORDER_DARK)
            self.main.configure(fg_color=CARD_DARK, border_width=1, border_color=BORDER_DARK)
            self.header.configure(fg_color=CARD_DARK, border_width=1, border_color=BORDER_DARK)
            self.body.configure(fg_color=CARD_DARK, border_width=0)
            self.workflow.configure(fg_color=CARD_DARK, border_width=1, border_color=BORDER_DARK)

            # text
            for w in [self.diag_title, self.title_label, self.wf_title, self.run_title]:
                w.configure(text_color=TEXT_LIGHT)
            for w in [self.tagline_label, self.wf_sub, self.run_desc, self.footer_left]:
                w.configure(text_color=MUTED_DARK)

            # log
            self.log_box.configure(fg_color=CARD_DARK, text_color=TEXT_LIGHT, border_color=BORDER_DARK)

            # pills / accents
            self.status_pill.configure(fg_color="#1E2230", border_color=BORDER_DARK)
            self.status_text.configure(text_color=TEXT_LIGHT)

            # logo wrap
            self.logo_wrap.configure(fg_color=CARD_DARK, border_width=1, border_color=BORDER_DARK)

            # buttons
            self.btn_run.configure(fg_color=ACCENT, hover_color="#F39C7A", text_color="white")
            self.btn_reset.configure(text_color=DANGER, border_color=BORDER_DARK, hover_color="#1E2230")

            # dots
            self.dot1.configure(text_color="#9CA3AF")
            self.dot2.configure(text_color="#22C55E")

    def _on_toggle_theme(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self._apply_theme("dark")
        else:
            ctk.set_appearance_mode("Light")
            self._apply_theme("light")

    # ---------------- STATUS / LOG ----------------
    def _set_status(self, state: str):
        # state: IDLE / WORKING / ERROR / OK
        state = state.upper().strip()
        self.status_text.configure(text=state)

        if state in ("IDLE",):
            pill = "#F2F2F2" if self._mode == "light" else "#1E2230"
            self.status_pill.configure(fg_color=pill)
        elif state in ("WORKING", "RUNNING"):
            self.status_pill.configure(fg_color="#F6C177" if self._mode == "light" else "#3B2E1E")
        elif state in ("OK", "DONE"):
            self.status_pill.configure(fg_color="#B7E4C7" if self._mode == "light" else "#1B3A2A")
        elif state in ("ERROR", "FAILED"):
            self.status_pill.configure(fg_color="#FECACA" if self._mode == "light" else "#3A1D1D")

    def _log(self, msg: str, kind: str = "info"):
        ts = time.strftime("[%H:%M:%S]")
        prefix = "→" if kind == "info" else ("✓" if kind == "ok" else "!" if kind == "warn" else "×")
        line = f"{ts} {prefix} {msg}\n"

        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="normal")  # keep editable feel like console

    def _set_current_file(self, path: str | None):
        self.current_file = path
        if path:
            self.file_value.configure(text=os.path.basename(path))
        else:
            self.file_value.configure(text="No file selected")

    def _refresh_buttons(self):
        # upload requires file + server ok
        can_upload = bool(self.current_file) and self.server_ok and not self.is_busy
        can_run = self.upload_ok and not self.is_busy
        can_download = not self.is_busy  # you can lock this to run-ok if you want

        if hasattr(self, "btn_upload"):
            self.btn_upload.configure(state=("normal" if can_upload else "disabled"))
        self.btn_run.configure(state=("normal" if can_run else "disabled"))
        if hasattr(self, "btn_download"):
            self.btn_download.configure(state=("normal" if can_download else "disabled"))

        # check/browse always allowed unless busy
        self.btn_check.configure(state=("normal" if not self.is_busy else "disabled"))
        self.btn_browse.configure(state=("normal" if not self.is_busy else "disabled"))
        self.btn_reset.configure(state=("normal" if not self.is_busy else "disabled"))

    # ---------------- LOGO ----------------
    def _load_logo(self):
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH).convert("RGBA")
                img = img.resize((26, 26))
                self._logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(26, 26))
                self.logo_label.configure(image=self._logo_img, text="")
                return
            except Exception:
                pass
        # fallback
        self.logo_label.configure(text="🐼")

    # ---------------- THREAD HELPERS ----------------
    def _run_bg(self, start_msg: str, work_fn, done_fn):
        if self.is_busy:
            return

        self.is_busy = True
        self._set_status("WORKING")
        self._refresh_buttons()
        self._log(start_msg, "info")

        def runner():
            try:
                ok, payload = work_fn()
            except Exception as e:
                ok, payload = False, str(e)

            def finish():
                self.is_busy = False
                done_fn(ok, payload)
                self._refresh_buttons()

            self.after(0, finish)

        threading.Thread(target=runner, daemon=True).start()

    # ---------------- ACTIONS (STUBS) ----------------
    def on_check_server(self):
        def work():
            time.sleep(0.6)  # simulate
            return True, "Secure connection established."
        def done(ok, payload):
            if ok:
                self.server_ok = True
                self._set_status("OK")
                self._log(payload, "ok")
            else:
                self.server_ok = False
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Connection request to inference engine…", work, done)

    def on_browse_zip(self):
        if self.is_busy:
            return
        path = filedialog.askopenfilename(
            title="Select ZIP dataset",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if not path:
            return
        self._set_current_file(path)
        self.upload_ok = False
        self._log(f"ZIP selected: {os.path.basename(path)}", "ok")
        self._set_status("IDLE")
        self._refresh_buttons()

    def on_upload(self):
        def work():
            time.sleep(0.8)  # simulate
            return True, "Upload completed. Dataset stored."
        def done(ok, payload):
            if ok:
                self.upload_ok = True
                self._set_status("OK")
                self._log(payload, "ok")
            else:
                self.upload_ok = False
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Uploading dataset…", work, done)

    def on_run_detection(self):
        def work():
            time.sleep(1.2)  # simulate
            return True, "Detection completed: 100%."
        def done(ok, payload):
            if ok:
                self._set_status("DONE")
                self._log(payload, "ok")
            else:
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Starting detection…", work, done)

    def on_download(self):
        def work():
            time.sleep(0.5)  # simulate
            return True, "CSV saved."
        def done(ok, payload):
            if ok:
                self._set_status("OK")
                self._log(payload, "ok")
            else:
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Downloading results…", work, done)

    def on_reset(self):
        if self.is_busy:
            return
        if not messagebox.askyesno("Reset Workspace", "This will delete temporary data.\nContinue?"):
            return

        def work():
            time.sleep(0.5)  # simulate
            return True, "Workspace cleared."
        def done(ok, payload):
            if ok:
                self.current_file = None
                self.server_ok = False
                self.upload_ok = False
                self._set_current_file(None)
                self._set_status("IDLE")
                self._log(payload, "ok")
            else:
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Resetting workspace…", work, done)


if __name__ == "__main__":
    PandaScanApp().mainloop()
