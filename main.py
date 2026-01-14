# PANDA SCAN — Tkinter UI
# - Header image as background (banner)
# - Scrollable body so buttons never get hidden
# - Opens initially sized to fit content (within screen limits)
#
# Requirements (recommended):
#   pip install pillow
#
# Put your header image here:
#   assets/panda_header.png  (or change HEADER_IMAGE path below)

import os
import sys
import threading
import ctypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Pillow for high-quality image resize
try:
    from PIL import Image, ImageTk  # type: ignore
    HAS_PIL = True
except Exception:
    HAS_PIL = False


def make_dpi_aware_windows():
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class ScrollableFrame(ttk.Frame):
    """
    Κλασικό scrollable container:
    Canvas + vertical scrollbar + inner frame.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        # update scrollregion
        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # mouse wheel scroll
        self._bind_mousewheel(self.canvas)

    def _on_frame_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        # make inner frame width match canvas width
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def _bind_mousewheel(self, widget):
        def _on_mousewheel(event):
            # Windows / Mac
            if event.delta:
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            else:
                # Linux (Button-4/5)
                if event.num == 4:
                    self.canvas.yview_scroll(-3, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(3, "units")

        # Windows/Mac
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        # Linux
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)


class PandaScanUI:
    # Palette
    BG = "#F4F1EC"
    CARD = "#FFF8F2"
    CARD_BORDER = "#E9DED4"
    TEXT = "#1F2328"
    MUTED = "#5E6772"

    RUN = "#FF7A00"
    RUN_HOVER = "#FF8E2B"
    DANGER = "#C62828"
    DANGER_HOVER = "#E53935"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PANDA SCAN")
        self.root.configure(bg=self.BG)

        # State
        self.zip_path: str | None = None
        self.is_busy = False

        # Assets
        # Βάλε εδώ τη header εικόνα σου (ιδανικά wide banner).
        self.HEADER_IMAGE = self._first_existing([
            "assets/panda_header.png",
            "assets/header.png",
            "panda.png",
            "header.png",
        ])

        self._setup_style()

        # Layout: Header (fixed) + Body (scrollable)
        self._build_header()
        self._build_body()

        # Initial size so everything fits (and if not, scroll kicks in)
        self.root.after(50, self._fit_to_content)

    # ----------------------- Styling -----------------------
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.FONT = ("Segoe UI", 12)
        self.FONT_SM = ("Segoe UI", 11)
        self.FONT_MD_B = ("Segoe UI Semibold", 12)
        self.FONT_LG_B = ("Segoe UI Semibold", 22)

        self.root.option_add("*Font", self.FONT)

        style.configure("PS.TButton", padding=(12, 8))
        style.configure("PS.Small.TButton", padding=(12, 7), font=self.FONT_SM)

        style.configure(
            "PS.Primary.TButton",
            padding=(16, 11),
            background=self.RUN,
            foreground="#FFFFFF",
            font=("Segoe UI Semibold", 12),
        )
        style.map("PS.Primary.TButton", background=[("active", self.RUN_HOVER)])

        style.configure(
            "PS.Danger.TButton",
            padding=(12, 8),
            background=self.DANGER,
            foreground="#FFFFFF",
            font=("Segoe UI Semibold", 12),
        )
        style.map("PS.Danger.TButton", background=[("active", self.DANGER_HOVER)])

    # ----------------------- Header (image background) -----------------------
    def _build_header(self):
        # Header container
        self.header = tk.Frame(self.root, bg="#000000")
        self.header.pack(fill="x")

        # Banner canvas (image as background)
        self.banner_h = 600  # height of header banner
        self.banner = tk.Canvas(self.header, height=self.banner_h, highlightthickness=0, bd=0)
        self.banner.pack(fill="x")

        # Overlay texts on banner

        self.status_var = tk.StringVar(value="Κατάσταση: Αναμονή…")
        self.status_lbl = tk.Label(
            self.banner, textvariable=self.status_var,
            fg="#E6E6E6", bg="#000000",
            font=("Segoe UI", 12)
        )

        self.banner_title_id = self.banner.create_window(0, 0, anchor="center", window=self.title_lbl)
        self.banner_sub_id = self.banner.create_window(0, 0, anchor="center", window=self.subtitle_lbl)
        self.banner_status_id = self.banner.create_window(0, 0, anchor="center", window=self.status_lbl)

        # Load base image if available
        self._banner_img_base = None
        self._banner_img_tk = None
        # Load base image (no scaling on resize)
        self._banner_img_base = None
        self._banner_img_tk = None

        if self.HEADER_IMAGE and HAS_PIL:
            try:
                self._banner_img_base = Image.open(self.HEADER_IMAGE).convert("RGBA")

                # αν θες, κάνε ΕΝΑ resize ΜΟΝΟ ΜΙΑ ΦΟΡΑ (π.χ. λίγο μικρότερο)
                # αλλιώς άστο όπως είναι
                # self._banner_img_base = self._banner_img_base.resize((900, 220), Image.LANCZOS)

                self._banner_img_tk = ImageTk.PhotoImage(self._banner_img_base)
            except Exception:
                self._banner_img_base = None
                self._banner_img_tk = None

        # Resize handler
        self.banner.bind("<Configure>", self._redraw_banner)

    def _redraw_banner(self, event=None):
        """
        Redraw banner background to fill width, crop nicely (cover-like).
        Also re-position overlay labels.
        """
        w = self.banner.winfo_width()
        h = self.banner_h

        # Background:
        w = self.banner.winfo_width()
        h = self.banner_h

        # solid background
        self.banner.delete("bg")
        self.banner.create_rectangle(0, 0, w, h, fill="#111111", width=0, tags="bg")

        # draw image centered, NO scaling
        if self._banner_img_tk:
            self.banner.delete("img")
            self.banner.create_image(
                w // 2, h // 2,
                image=self._banner_img_tk,
                anchor="center",
                tags="img"
            )

        # (optional) dark overlay for readability
        self.banner.delete("overlay")
        self.banner.create_rectangle(0, 0, w, h, fill="#000000", stipple="gray50", width=0, tags="overlay")

        # Place overlay labels (centered)
        cx = w // 2
        self.banner.coords(self.banner_title_id, cx, 62)
        self.banner.coords(self.banner_sub_id, cx, 102)
        self.banner.coords(self.banner_status_id, cx, 142)

        # Ensure text labels background matches overlay
        # (helps readability even without image)
        for lbl in (self.title_lbl, self.subtitle_lbl, self.status_lbl):
            lbl.configure(bg="#000000")

    @staticmethod
    def _cover_resize(img: "Image.Image", target_w: int, target_h: int) -> "Image.Image":
        """Resize/crop image to COVER the target area."""
        iw, ih = img.size
        scale = max(target_w / iw, target_h / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        resized = img.resize((nw, nh), Image.LANCZOS)
        left = (nw - target_w) // 2
        top = (nh - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    # ----------------------- Body (scrollable) -----------------------
    def _build_body(self):
        # Scrollable container
        self.body = ScrollableFrame(self.root)
        self.body.pack(fill="both", expand=True)

        inner = self.body.inner

        # Body background
        # ttk.Frame inherits style; easiest is to put a tk.Frame as wrapper:
        wrapper = tk.Frame(inner, bg=self.BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=18)

        # Card
        card = tk.Frame(
            wrapper, bg=self.CARD,
            highlightthickness=1, highlightbackground=self.CARD_BORDER
        )
        card.pack(fill="x", expand=True)

        # Card grid
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        tk.Label(
            card, text="Βήματα",
            bg=self.CARD, fg=self.TEXT,
            font=("Segoe UI Semibold", 16),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        r = 1
        r = self._step_row(card, r, "Έλεγχος server", "Ελέγχει αν ο server είναι διαθέσιμος.", "CHECK", self.on_check)
        r = self._step_row(card, r, "Επιλογή ZIP", "Διάλεξε zip με εικόνες για ανάλυση.", "BROWSE", self.on_browse)
        r = self._step_row(card, r, "Upload", "Ανέβασε το zip στον server.", "UPLOAD", self.on_upload, store="upload")
        r = self._step_row(card, r, "Download results", "Κατέβασε CSV με αποτελέσματα.", "DOWNLOAD", self.on_download, store="download")

        # Separator
        ttk.Separator(card, orient="horizontal").grid(row=r, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 14))
        r += 1

        # Danger zone
        tk.Label(
            card, text="Danger zone",
            bg=self.CARD, fg=self.TEXT,
            font=("Segoe UI Semibold", 14),
        ).grid(row=r, column=0, sticky="w", padx=18)
        r += 1

        tk.Label(
            card, text="Διαγράφει όλα τα προσωρινά δεδομένα από τον φάκελο εργασίας.",
            bg=self.CARD, fg=self.MUTED, font=self.FONT_SM
        ).grid(row=r, column=0, sticky="w", padx=18, pady=(4, 10))

        self.btn_reset = ttk.Button(card, text="ΕΚΚΑΘΑΡΙΣΗ ΜΝΗΜΗΣ", style="PS.Danger.TButton", command=self.on_reset_confirm)
        self.btn_reset.grid(row=r, column=1, sticky="e", padx=18, pady=(0, 10))
        r += 1

        # Primary Run button (always accessible; if window small -> scroll)
        bottom = tk.Frame(wrapper, bg=self.BG)
        bottom.pack(fill="x", pady=(18, 0))

        self.btn_run = ttk.Button(bottom, text="▶  ΕΚΤΕΛΕΣΗ ΑΝΑΛΥΣΗΣ", style="PS.Primary.TButton", command=self.on_run)
        self.btn_run.pack(pady=(0, 8))

        self.file_hint_var = tk.StringVar(value="ZIP: (κανένα)")
        tk.Label(bottom, textvariable=self.file_hint_var, bg=self.BG, fg=self.MUTED, font=self.FONT_SM).pack()

        self._set_ready_state()

    def _step_row(self, parent, row, title, desc, btn_text, cmd, store=None):
        box = tk.Frame(parent, bg=self.CARD)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=18, pady=8)
        box.columnconfigure(0, weight=1)

        left = tk.Frame(box, bg=self.CARD)
        left.grid(row=0, column=0, sticky="w")

        tk.Label(left, text=title, bg=self.CARD, fg=self.TEXT, font=("Segoe UI Semibold", 13)).pack(anchor="w")
        tk.Label(left, text=desc, bg=self.CARD, fg=self.MUTED, font=self.FONT_SM).pack(anchor="w", pady=(2, 0))

        btn = ttk.Button(box, text=btn_text, style="PS.Small.TButton", command=cmd)
        btn.grid(row=0, column=1, sticky="e")

        if store == "upload":
            self.btn_upload = btn
        if store == "download":
            self.btn_download = btn

        return row + 1

    # ----------------------- Fit window to content -----------------------
    def _fit_to_content(self):
        """
        Ανοίγει το παράθυρο έτσι ώστε να χωράει όλο το UI.
        Αν η οθόνη είναι μικρή, κρατά safe μέγεθος και το scroll κάνει τη δουλειά.
        """
        self.root.update_idletasks()

        req_w = self.root.winfo_reqwidth()
        req_h = self.root.winfo_reqheight()

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        # margins from screen edges
        max_w = int(sw * 0.88)
        max_h = int(sh * 0.88)

        w = min(max(req_w, 860), max_w)
        h = min(max(req_h, 680), max_h)

        self.root.geometry(f"{w}x{h}")

    # ----------------------- UX helpers -----------------------
    def _set_ready_state(self):
        if hasattr(self, "btn_upload"):
            self.btn_upload.configure(state="normal" if self.zip_path else "disabled")
        self.file_hint_var.set(f"ZIP: {Path(self.zip_path).name}" if self.zip_path else "ZIP: (κανένα)")

    def _set_busy(self, busy: bool, status: str | None = None):
        self.is_busy = busy
        if status is not None:
            self.status_var.set(status)

        state = "disabled" if busy else "normal"
        self.btn_run.configure(state=state)
        self.btn_reset.configure(state=state)
        if hasattr(self, "btn_upload"):
            self.btn_upload.configure(state=state if (self.zip_path and not busy) else "disabled")
        if hasattr(self, "btn_download"):
            self.btn_download.configure(state=state)

        self.root.update_idletasks()

    def _bg_task(self, work_fn, done_fn):
        def runner():
            try:
                ok, msg = work_fn()
            except Exception as e:
                ok, msg = False, str(e)
            self.root.after(0, lambda: done_fn(ok, msg))

        threading.Thread(target=runner, daemon=True).start()

    # ----------------------- Actions (stubs) -----------------------
    def on_check(self):
        if self.is_busy:
            return
        self._set_busy(True, "Κατάσταση: Έλεγχος σύνδεσης…")

        def work():
            # TODO: βάλε εδώ το πραγματικό connection check
            return True, "Server OK"

        def done(ok, msg):
            self._set_busy(False, f"Κατάσταση: {'✅' if ok else '❌'} {msg}")

        self._bg_task(work, done)

    def on_browse(self):
        if self.is_busy:
            return
        path = filedialog.askopenfilename(
            title="Επιλογή ZIP",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")]
        )
        if not path:
            return

        self.zip_path = path
        self.status_var.set(f"Κατάσταση: ✅ Επιλέχθηκε {Path(path).name}")
        self._set_ready_state()

    def on_upload(self):
        if self.is_busy:
            return
        if not self.zip_path:
            messagebox.showwarning("ZIP", "Διάλεξε πρώτα ZIP.")
            return

        self._set_busy(True, "Κατάσταση: Upload σε εξέλιξη…")

        def work():
            # TODO: FileSender(...).send_file()
            return True, "Upload OK"

        def done(ok, msg):
            self._set_busy(False, f"Κατάσταση: {'✅' if ok else '❌'} {msg}")
            self._set_ready_state()

        self._bg_task(work, done)

    def on_download(self):
        if self.is_busy:
            return
        self._set_busy(True, "Κατάσταση: Λήψη αποτελεσμάτων…")

        def work():
            # TODO: api.download()
            return True, "CSV saved"

        def done(ok, msg):
            self._set_busy(False, f"Κατάσταση: {'✅' if ok else '❌'} {msg}")

        self._bg_task(work, done)

    def on_run(self):
        if self.is_busy:
            return
        if not self.zip_path:
            messagebox.showwarning("ZIP", "Διάλεξε πρώτα ZIP για ανάλυση.")
            return

        self._set_busy(True, "Κατάσταση: Εκτέλεση ανάλυσης…")

        def work():
            # TODO: api.run()
            return True, "Detection completed"

        def done(ok, msg):
            self._set_busy(False, f"Κατάσταση: {'✅' if ok else '❌'} {msg}")

        self._bg_task(work, done)

    def on_reset_confirm(self):
        if self.is_busy:
            return

        confirm = messagebox.askyesno(
            "Εκκαθάριση μνήμης",
            "Θα διαγραφούν ΟΛΑ τα προσωρινά δεδομένα.\n\nΣυνέχεια;"
        )
        if not confirm:
            return

        self._set_busy(True, "Κατάσταση: Εκκαθάριση μνήμης…")

        def work():
            # TODO: cleanup logic
            return True, "Workspace cleared"

        def done(ok, msg):
            self._set_busy(False, f"Κατάσταση: {'✅' if ok else '❌'} {msg}")
            self._set_ready_state()

        self._bg_task(work, done)

    # ----------------------- Utilities -----------------------
    @staticmethod
    def _first_existing(paths: list[str]) -> str | None:
        for p in paths:
            if p and os.path.exists(p):
                return p
        return None


def main():
    make_dpi_aware_windows()
    root = tk.Tk()
    PandaScanUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
