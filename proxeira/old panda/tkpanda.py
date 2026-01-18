import ctypes
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# Optional Pillow for nicer PNG resize
try:
    from PIL import Image, ImageTk  # type: ignore
    HAS_PIL = True
except Exception:
    HAS_PIL = False


APP_TITLE = "PANDA SCAN"
TAGLINE = "SMART IMAGE DETECTION • CLEAN & QUIET"
VERSION_TEXT = "VERSION 1.0.4 • OFFLINE"

LOGO_PATH = "../../panda.png"  # βάλε εδώ το panda logo (png)

# --- Colors (Monochrome Pro: b/w + one accent) ---
LIGHT = {
    "bg": "#F6F3EE",
    "card": "#FFFFFF",
    "text": "#1F2328",
    "muted": "#6B7280",
    "border": "#E7E3DC",
    "pill": "#F2F2F2",
    "accent": "#F08A5D",  # primary
    "danger": "#E14B4B",  # reset
}

DARK = {
    "bg": "#0F1115",
    "card": "#151923",
    "text": "#EAECEF",
    "muted": "#A1A1AA",
    "border": "#262B36",
    "pill": "#1E2230",
    "accent": "#F08A5D",
    "danger": "#E14B4B",
}


def make_dpi_aware_windows():
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

class Scrollable(ttk.Frame):
    """Scrollable container for the MAIN area (so buttons never get hidden)."""
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._bind_mousewheel()

    def _on_frame_configure(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def _bind_mousewheel(self):
        def on_wheel(e):
            if e.delta:
                self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            else:
                if e.num == 4:
                    self.canvas.yview_scroll(-3, "units")
                elif e.num == 5:
                    self.canvas.yview_scroll(3, "units")

        self.canvas.bind_all("<MouseWheel>", on_wheel)
        self.canvas.bind_all("<Button-4>", on_wheel)
        self.canvas.bind_all("<Button-5>", on_wheel)


class PandaScanTk:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x780")
        self.root.minsize(980, 640)

        # State
        self.current_file: str | None = None
        self.server_ok = False
        self.upload_ok = False
        self.is_busy = False

        # Theme
        self.mode = "light"
        self.colors = LIGHT

        # ttk style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._build()
        self._apply_theme()

        self._set_status("IDLE")
        self._refresh_buttons()
        self._log("App ready.")

    # ---------------- UI BUILD ----------------
    def _build(self):
        self.root.grid_columnconfigure(0, weight=0)  # left fixed
        self.root.grid_columnconfigure(1, weight=1)  # right expand
        self.root.grid_rowconfigure(0, weight=1)

        # LEFT: Diagnostics
        self.left = ttk.Frame(self.root)
        self.left.grid(row=0, column=0, sticky="nsw", padx=(20, 12), pady=20)
        self.left.configure(width=330)
        self.left.grid_propagate(False)
        self.left.grid_rowconfigure(1, weight=1)
        self.left.grid_columnconfigure(0, weight=1)

        self.diag_top = ttk.Frame(self.left)
        self.diag_top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))
        self.diag_top.grid_columnconfigure(0, weight=1)

        self.diag_title = ttk.Label(self.diag_top, text="SYSTEM DIAGNOSTICS")
        self.diag_title.grid(row=0, column=0, sticky="w")

        self.diag_dots = ttk.Frame(self.diag_top)
        self.diag_dots.grid(row=0, column=1, sticky="e")

        self.dot1 = tk.Label(self.diag_dots, text="●", font=("Segoe UI", 12))
        self.dot2 = tk.Label(self.diag_dots, text="●", font=("Segoe UI", 12))
        self.dot1.pack(side="left", padx=(0, 6))
        self.dot2.pack(side="left")

        # Log text + scrollbar
        self.log_frame = ttk.Frame(self.left)
        self.log_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(self.log_frame, wrap="word", bd=0, highlightthickness=0)
        self.log_scroll = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)

        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_scroll.grid(row=0, column=1, sticky="ns")

        # RIGHT: Main container (header + scrollable body)
        self.main = ttk.Frame(self.root)
        self.main.grid(row=0, column=1, sticky="nsew", padx=(12, 20), pady=20)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ttk.Frame(self.main)
        self.header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        self.header.grid_columnconfigure(1, weight=1)

        # Logo square
        self.logo_box = tk.Frame(self.header, width=56, height=56, bd=0, highlightthickness=1)
        self.logo_box.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="w")
        self.logo_box.grid_propagate(False)

        self.logo_lbl = tk.Label(self.logo_box, text="")
        self.logo_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self._load_logo()

        # Title + tagline
        self.title_lbl = ttk.Label(self.header, text=APP_TITLE)
        self.title_lbl.grid(row=0, column=1, sticky="w", pady=(18, 0))

        self.tag_lbl = ttk.Label(self.header, text=TAGLINE)
        self.tag_lbl.grid(row=1, column=1, sticky="w", pady=(2, 18))

        # Right controls: dark toggle + status pill
        self.right_controls = ttk.Frame(self.header)
        self.right_controls.grid(row=0, column=2, rowspan=2, padx=16, pady=16, sticky="e")

        self.var_dark = tk.IntVar(value=0)
        self.dark_toggle = ttk.Checkbutton(self.right_controls, text="DARK", variable=self.var_dark, command=self._toggle_theme)
        self.dark_toggle.pack(side="right", padx=(10, 0))

        # Status pill (canvas so it looks rounded on ttk)
        self.pill = tk.Canvas(self.right_controls, width=110, height=32, bd=0, highlightthickness=0)
        self.pill.pack(side="right")
        self.pill_text = self.pill.create_text(55, 16, text="IDLE", font=("Segoe UI Semibold", 10))

        # Scrollable body
        self.scroll = Scrollable(self.main)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=18, pady=(12, 18))

        self.body_wrap = tk.Frame(self.scroll.inner, bd=0, highlightthickness=0)
        self.body_wrap.pack(fill="both", expand=True, padx=16, pady=16)

        # Workflow card
        self.workflow = tk.Frame(self.body_wrap, bd=0, highlightthickness=1)
        self.workflow.pack(fill="x", expand=True)

        # Workflow header row
        wf_head = tk.Frame(self.workflow, bd=0, highlightthickness=0)
        wf_head.pack(fill="x", padx=18, pady=(18, 10))
        wf_head.grid_columnconfigure(0, weight=1)

        left = tk.Frame(wf_head, bd=0, highlightthickness=0)
        left.grid(row=0, column=0, sticky="w")

        self.wf_title = tk.Label(left, text="Analysis Workflow", font=("Segoe UI Semibold", 14))
        self.wf_title.pack(anchor="w")

        self.wf_sub = tk.Label(left, text="Follow the steps to process your dataset.", font=("Segoe UI", 11))
        self.wf_sub.pack(anchor="w", pady=(4, 0))

        # Current file box
        self.file_box = tk.Frame(wf_head, bd=0, highlightthickness=1)
        self.file_box.grid(row=0, column=1, sticky="e", padx=(12, 0))

        self.file_title = tk.Label(self.file_box, text="CURRENT FILE", font=("Segoe UI Semibold", 9))
        self.file_value = tk.Label(self.file_box, text="No file selected", font=("Segoe UI", 11))
        self.file_title.pack(anchor="w", padx=12, pady=(10, 0))
        self.file_value.pack(anchor="w", padx=12, pady=(4, 10))

        # Steps
        self.step1_btn = self._step_row("1. System Check", "Verify connection to the inference engine.", "Check Server", self.on_check)
        self.step2_btn = self._step_row("2. Select Dataset", "Choose a ZIP file containing images.", "Browse ZIP", self.on_browse)
        self.step3_btn = self._step_row("3. Upload to Cloud", "Securely transfer data for processing.", "Upload", self.on_upload)

        # Run block (primary CTA)
        run_block = tk.Frame(self.workflow, bd=0, highlightthickness=0)
        run_block.pack(fill="x", padx=18, pady=(8, 10))

        self.run_title = tk.Label(run_block, text="4. Run Detection", font=("Segoe UI Semibold", 14))
        self.run_desc = tk.Label(run_block, text="Start the AI analysis on the uploaded dataset.", font=("Segoe UI", 11))
        self.run_title.pack(anchor="center", pady=(12, 4))
        self.run_desc.pack(anchor="center", pady=(0, 12))

        self.btn_run = tk.Button(run_block, text="▶  RUN DETECTION", command=self.on_run, relief="flat", bd=0, padx=18, pady=10)
        self.btn_run.pack(anchor="center", pady=(0, 14))

        # Results row
        self.step5_btn = self._step_row("5. Results", "Download the generated CSV report.", "Download CSV", self.on_download)

        # Footer inside workflow (version + reset)
        footer = tk.Frame(self.workflow, bd=0, highlightthickness=0)
        footer.pack(fill="x", padx=18, pady=(6, 16))
        footer.grid_columnconfigure(0, weight=1)

        self.footer_left = tk.Label(footer, text=VERSION_TEXT, font=("Segoe UI", 10))
        self.footer_left.grid(row=0, column=0, sticky="w")

        self.btn_reset = tk.Button(footer, text="🗑  Reset Workspace", command=self.on_reset, relief="flat", bd=0, padx=12, pady=8)
        self.btn_reset.grid(row=0, column=1, sticky="e")

    def _step_row(self, title, desc, btn_text, cmd):
        row = tk.Frame(self.workflow, bd=0, highlightthickness=0)
        row.pack(fill="x", padx=18, pady=8)
        row.grid_columnconfigure(0, weight=1)

        # Left text
        left = tk.Frame(row, bd=0, highlightthickness=0)
        left.grid(row=0, column=0, sticky="w")

        t = tk.Label(left, text=title, font=("Segoe UI Semibold", 12))
        d = tk.Label(left, text=desc, font=("Segoe UI", 11))
        t.pack(anchor="w")
        d.pack(anchor="w", pady=(2, 0))

        # Right button
        b = ttk.Button(row, text=btn_text, command=cmd)
        b.grid(row=0, column=1, sticky="e")
        return b

    # ---------------- THEME ----------------
    def _apply_theme(self):
        c = self.colors

        # Root backgrounds
        self.root.configure(bg=c["bg"])
        self.body_wrap.configure(bg=c["bg"])

        # Left panel look (ttk frames don’t always accept bg on Windows; use underlying tk widgets too)
        self.left.configure(style="Card.TFrame")
        self.main.configure(style="Card.TFrame")
        self.header.configure(style="Card.TFrame")

        # Configure ttk styles
        self.style.configure("Card.TFrame", background=c["card"])
        self.style.configure("TFrame", background=c["card"])
        self.style.configure("TLabel", background=c["card"], foreground=c["text"], font=("Segoe UI", 11))
        self.style.configure("TButton", padding=(12, 7))

        # Left panel tk parts
        self.left.configure()
        for w in (self.diag_top, self.log_frame):
            w.configure(style="Card.TFrame")

        # Diagnostics labels
        self.diag_title.configure(foreground=c["muted"], background=c["card"], font=("Segoe UI Semibold", 10))
        self.dot1.configure(bg=c["card"], fg="#9CA3AF")
        self.dot2.configure(bg=c["card"], fg="#22C55E")

        # Log textbox
        self.log_text.configure(bg=c["card"], fg=c["text"], insertbackground=c["text"])
        self.log_text.tag_configure("ok", foreground="#16A34A")
        self.log_text.tag_configure("err", foreground=c["danger"])
        self.log_text.tag_configure("info", foreground=c["muted"])

        # Header tk logo box
        self.logo_box.configure(bg=c["card"], highlightbackground=c["border"])
        self.logo_lbl.configure(bg=c["card"], fg=c["text"])

        # Header labels
        self.title_lbl.configure(style="Title.TLabel")
        self.tag_lbl.configure(style="Muted.TLabel")
        self.style.configure("Title.TLabel", font=("Segoe UI Semibold", 22), background=c["card"], foreground=c["text"])
        self.style.configure("Muted.TLabel", font=("Segoe UI", 10), background=c["card"], foreground=c["muted"])

        # Status pill
        self.pill.configure(bg=c["card"])
        self._draw_pill("IDLE")  # redraw with current theme colors

        # Workflow card
        self.workflow.configure(bg=c["card"], highlightbackground=c["border"])
        for w in (self.wf_title, self.run_title):
            w.configure(bg=c["card"], fg=c["text"])
        for w in (self.wf_sub, self.run_desc, self.footer_left):
            w.configure(bg=c["card"], fg=c["muted"])
        self.file_box.configure(bg=c["card"], highlightbackground=c["border"])
        self.file_title.configure(bg=c["card"], fg=c["muted"])
        self.file_value.configure(bg=c["card"], fg=c["text"])

        # Step rows: all labels inside workflow are tk.Label -> ensure correct colors
        def recolor_children(container):
            for child in container.winfo_children():
                if isinstance(child, tk.Label):
                    # detect muted text by font size/weight heuristic is messy; keep default:
                    if "Semibold" in str(child.cget("font")):
                        child.configure(bg=c["card"], fg=c["text"])
                    else:
                        # descriptions
                        child.configure(bg=c["card"], fg=c["muted"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=c["card"])
                    recolor_children(child)
        recolor_children(self.workflow)

        # Primary button (Run)
        self.btn_run.configure(bg=c["accent"], fg="white", activebackground=c["accent"], activeforeground="white", cursor="hand2")

        # Reset button (danger text, minimal)
        self.btn_reset.configure(bg=c["card"], fg=c["danger"], activebackground=c["card"], activeforeground=c["danger"], cursor="hand2")

        # Background for scroll canvas
        self.scroll.canvas.configure(bg=c["bg"])
        self.scroll.inner.configure(style="Card.TFrame")
        self.scroll.canvas.update_idletasks()

    def _toggle_theme(self):
        if self.var_dark.get() == 1:
            self.mode = "dark"
            self.colors = DARK
        else:
            self.mode = "light"
            self.colors = LIGHT
        self._apply_theme()

    # ---------------- STATUS / LOG ----------------
    def _draw_pill(self, text):
        c = self.colors
        self.pill.delete("all")
        w, h = 110, 32
        r = 16
        # rounded rect
        self._round_rect(self.pill, 2, 2, w-2, h-2, r, fill=c["pill"], outline=c["border"])
        self.pill_text = self.pill.create_text(w//2, h//2, text=text, fill=c["text"], font=("Segoe UI Semibold", 10))

    @staticmethod
    def _round_rect(canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _set_status(self, state: str):
        self.status_state = state.upper()
        # change pill color by state (subtle)
        c = self.colors
        if self.status_state == "IDLE":
            c["pill"] = "#F2F2F2" if self.mode == "light" else "#1E2230"
        elif self.status_state in ("WORKING", "RUNNING"):
            c["pill"] = "#F6C177" if self.mode == "light" else "#3B2E1E"
        elif self.status_state in ("OK", "DONE"):
            c["pill"] = "#B7E4C7" if self.mode == "light" else "#1B3A2A"
        elif self.status_state in ("ERROR", "FAILED"):
            c["pill"] = "#FECACA" if self.mode == "light" else "#3A1D1D"
        self._draw_pill(self.status_state)

    def _log(self, msg: str, kind: str = "info"):
        ts = time.strftime("[%H:%M:%S]")
        prefix = "→" if kind == "info" else ("✓" if kind == "ok" else "×")
        line = f"{ts} {prefix} {msg}\n"
        self.log_text.insert("end", line, kind)
        self.log_text.see("end")

    def _set_current_file(self, path: str | None):
        self.current_file = path
        self.file_value.configure(text=os.path.basename(path) if path else "No file selected")

    # ---------------- STATE / BUTTONS ----------------
    def _refresh_buttons(self):
        can_upload = bool(self.current_file) and self.server_ok and not self.is_busy
        can_run = self.upload_ok and not self.is_busy

        self.step3_btn.configure(state=("normal" if can_upload else "disabled"))
        self.btn_run.configure(state=("normal" if can_run else "disabled"))

        # basic lock while busy
        self.step1_btn.configure(state=("disabled" if self.is_busy else "normal"))
        self.step2_btn.configure(state=("disabled" if self.is_busy else "normal"))
        self.step5_btn.configure(state=("disabled" if self.is_busy else "normal"))

        self.btn_reset.configure(state=("disabled" if self.is_busy else "normal"))

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

            self.root.after(0, finish)

        threading.Thread(target=runner, daemon=True).start()

    # ---------------- LOGO ----------------
    def _load_logo(self):
        if os.path.exists(LOGO_PATH) and HAS_PIL:
            try:
                img = Image.open(LOGO_PATH).convert("RGBA")
                img = img.resize((26, 26), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                self.logo_lbl.configure(image=self._logo_img, text="")
                return
            except Exception:
                pass
        self.logo_lbl.configure(text="🐼")

    # ---------------- ACTIONS (STUBS) ----------------
    def on_check(self):
        def work():
            time.sleep(0.6)
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

    def on_browse(self):
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
        self._set_status("IDLE")
        self._log(f"ZIP selected: {Path(path).name}", "ok")
        self._refresh_buttons()

    def on_upload(self):
        def work():
            time.sleep(0.8)
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

    def on_run(self):
        def work():
            time.sleep(1.2)
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
            time.sleep(0.5)
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
            time.sleep(0.5)
            return True, "Workspace cleared."
        def done(ok, payload):
            if ok:
                self._set_current_file(None)
                self.server_ok = False
                self.upload_ok = False
                self._set_status("IDLE")
                self._log(payload, "ok")
            else:
                self._set_status("ERROR")
                self._log(payload, "err")
            self._refresh_buttons()
        self._run_bg("Resetting workspace…", work, done)


def main():
    make_dpi_aware_windows()
    root = tk.Tk()
    app = PandaScanTk(root)
    root.mainloop()



if __name__ == "__main__":
    main()
