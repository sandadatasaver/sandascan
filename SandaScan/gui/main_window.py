"""
SandaScan Main Window

Professional desktop GUI for document restoration built with CustomTkinter.

Features:
- Drag & drop file/folder input
- Before/after preview panel
- Batch processing with progress bar
- Configurable pipeline settings
- Dark mode
- Keyboard shortcuts
"""

import os
import sys
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from typing import List, Optional, Callable
from pathlib import Path

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk

from ..core.pipeline import PipelineConfig, PipelineStep
from ..core.batch import BatchProcessor, BatchResult


# ── Auto-detect bundled tessdata folder ──────────────────────────────────
# This is needed for tesserocr on Linux/Mac. Windows uses pytesseract.
_bundle_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_candidate_tessdata = os.path.join(os.path.dirname(_bundle_root), "tessdata")
if os.path.isdir(_candidate_tessdata):
    os.environ.setdefault("TESSDATA_PREFIX", _candidate_tessdata)


# ── Appearance ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Constants ──────────────────────────────────────────────────────────────
APP_NAME = "SandaScan"
APP_VERSION = "1.0.3"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
SUPPORTED_FORMATS = (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp")

# ── Check OCR availability at startup ────────────────────────────────────
_OCR_AVAILABLE = False
_OCR_MESSAGE = ""
# Search common Tesseract binary paths
_TESSERACT_CANDIDATE_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]

def _find_tesseract_binary() -> Optional[str]:
    """Find the Tesseract executable path."""
    for path in _TESSERACT_CANDIDATE_PATHS:
        if os.path.exists(path):
            return path
    # Also check if 'tesseract' is in PATH
    result = shutil.which("tesseract")
    if result is not None:
        return result
    return None

def _check_ocr():
    global _OCR_AVAILABLE, _OCR_MESSAGE
    try:
        import pytesseract
        # Try 1: pytesseract finds Tesseract naturally
        try:
            pytesseract.get_tesseract_version()
            _OCR_AVAILABLE = True
            _OCR_MESSAGE = "✅  OCR ready"
            return
        except Exception:
            # Try 2: Manually point pytesseract to the binary
            tess_path = _find_tesseract_binary()
            if tess_path:
                pytesseract.pytesseract.tesseract_cmd = tess_path
                try:
                    pytesseract.get_tesseract_version()
                    _OCR_AVAILABLE = True
                    _OCR_MESSAGE = "✅  OCR ready (configured)"
                    return
                except Exception:
                    pass
            # Binary found but still failing — possibly TESSDATA issue
            _OCR_MESSAGE = (
                "⚠️  Tesseract found but not working.\n"
                "    Try adding to PATH manually:\n"
                "    set PATH=C:\\Program Files\\Tesseract-OCR;%PATH%"
            )
            return
    except ImportError:
        pass

    # pytesseract not installed at all
    tess_path = _find_tesseract_binary()
    if tess_path:
        _OCR_MESSAGE = "⚠️  Run: pip install pytesseract"
    else:
        _OCR_MESSAGE = (
            "⚠️  Tesseract not found.\n"
            "    1️⃣ Install from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "    2️⃣ pip install pytesseract"
        )

_check_ocr()


class SandaScanApp(ctk.CTk):
    """
    SandaScan main application window.
    """

    def __init__(self):
        super().__init__()

        # ── Window Setup ───────────────────────────────────────────────
        self.title(f"{APP_NAME} v{APP_VERSION} — Document Restoration Suite")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(960, 600)

        # Center on screen
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - WINDOW_WIDTH) // 2
        y = (screen_h - WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

        # ── State ──────────────────────────────────────────────────────
        self.input_files: List[str] = []
        self.current_image_index: int = 0
        self.processed_images: List[np.ndarray] = []
        self.is_processing: bool = False

        # ── Build UI ───────────────────────────────────────────────────
        self._build_menu_bar()
        self._build_main_layout()

        # ── Keyboard Shortcuts ─────────────────────────────────────────
        self.bind("<Control-o>", lambda e: self._add_files())
        self.bind("<Control-f>", lambda e: self._add_folder())
        self.bind("<Control-p>", lambda e: self._start_processing())
        self.bind("<Control-s>", lambda e: self._export_pdf())
        self.bind("<Control-r>", lambda e: self._clear_all())
        self.bind("<Escape>", lambda e: self._clear_all())

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Menu Bar ──────────────────────────────────────────────────────────

    def _build_menu_bar(self):
        """Build the top menu bar."""
        self.menu_frame = ctk.CTkFrame(self, height=48, corner_radius=0)
        self.menu_frame.pack(fill="x", padx=0, pady=0)
        self.menu_frame.pack_propagate(False)

        # App logo/title
        logo_label = ctk.CTkLabel(
            self.menu_frame,
            text=f"  📄  {APP_NAME}",
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        logo_label.pack(side="left", padx=(16, 8), pady=8)

        # Separator
        sep = ctk.CTkFrame(self.menu_frame, width=2, fg_color="#555555")
        sep.pack(side="left", fill="y", padx=8, pady=6)

        # Action buttons
        self._add_menu_button("📂  Add Files", self._add_files)
        self._add_menu_button("📁  Add Folder", self._add_folder)
        self._add_menu_button("❌  Clear", self._clear_all)

        # Separator
        sep2 = ctk.CTkFrame(self.menu_frame, width=2, fg_color="#555555")
        sep2.pack(side="left", fill="y", padx=8, pady=6)

        self._add_menu_button("💾  Export PDF", self._export_pdf)

        # Separator
        sep3 = ctk.CTkFrame(self.menu_frame, width=2, fg_color="#555555")
        sep3.pack(side="left", fill="y", padx=8, pady=6)

        self._add_menu_button("❓  Help", self._show_help)
        self._add_menu_button("ℹ️  About", self._show_about)

        # Theme toggle on the right
        self.theme_btn = ctk.CTkButton(
            self.menu_frame,
            text="☀️",
            width=40,
            height=32,
            command=self._toggle_theme,
            font=ctk.CTkFont(size=13),
        )
        self.theme_btn.pack(side="right", padx=(4, 16), pady=6)

    def _add_menu_button(self, text: str, command: Callable):
        """Add a styled menu button."""
        btn = ctk.CTkButton(
            self.menu_frame,
            text=text,
            command=command,
            font=ctk.CTkFont(size=13),
            height=32,
        )
        btn.pack(side="left", padx=4, pady=6)

    # ── Main Layout ───────────────────────────────────────────────────────

    def _build_main_layout(self):
        """Build the three-panel main layout."""
        # Main container
        self.main_paned = ctk.CTkFrame(self)
        self.main_paned.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # ── Left Panel: File List ──────────────────────────────────────
        self.left_panel = ctk.CTkFrame(self.main_paned, width=280)
        self.left_panel.pack(side="left", fill="y", padx=(0, 4), pady=0)
        self.left_panel.pack_propagate(False)

        ctk.CTkLabel(
            self.left_panel,
            text="📋  Input Files",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(padx=12, pady=(12, 8), anchor="w")

        # Drop zone overlay hint
        self.drop_hint = ctk.CTkLabel(
            self.left_panel,
            text="Drop images here\nor use the menu above",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        )
        self.drop_hint.pack(padx=12, pady=4, anchor="w")

        # File listbox
        self.file_listbox = tk.Listbox(
            self.left_panel,
            bg="#2b2b2b",
            fg="#dddddd",
            selectbackground="#1f538d",
            selectforeground="#ffffff",
            font=("Segoe UI", 11),
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.file_listbox.pack(fill="both", expand=True, padx=8, pady=4)
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)

        # File count label
        self.file_count_label = ctk.CTkLabel(
            self.left_panel,
            text="0 files loaded",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        )
        self.file_count_label.pack(padx=12, pady=(4, 8), anchor="w")

        # ── Center Panel: Preview ─────────────────────────────────────
        self.center_panel = ctk.CTkFrame(self.main_paned)
        self.center_panel.pack(side="left", fill="both", expand=True, padx=4, pady=0)

        # Preview header
        preview_header = ctk.CTkFrame(self.center_panel, height=36, fg_color="transparent")
        preview_header.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            preview_header,
            text="🔍  Preview",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        # View toggle
        self.view_var = ctk.StringVar(value="before")
        self.view_toggle = ctk.CTkSegmentedButton(
            preview_header,
            values=["Before", "After"],
            variable=self.view_var,
            command=self._on_view_toggle,
            width=160,
        )
        self.view_toggle.pack(side="right")

        # Canvas for image display
        self.preview_canvas = ctk.CTkCanvas(
            self.center_panel,
            bg="#1e1e1e",
            highlightthickness=0,
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=8, pady=4)

        # Navigation
        nav_frame = ctk.CTkFrame(self.center_panel, height=36, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8, pady=(4, 8))

        self.prev_btn = ctk.CTkButton(
            nav_frame, text="◀  Previous", width=100,
            command=self._prev_image, state="disabled"
        )
        self.prev_btn.pack(side="left", padx=4)

        self.page_label = ctk.CTkLabel(
            nav_frame, text="No image", font=ctk.CTkFont(size=12)
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(
            nav_frame, text="Next  ▶", width=100,
            command=self._next_image, state="disabled"
        )
        self.next_btn.pack(side="right", padx=4)

        # ── Right Panel: Controls & Settings ──────────────────────────
        self.right_panel = ctk.CTkFrame(self.main_paned, width=280)
        self.right_panel.pack(side="right", fill="y", padx=(4, 0), pady=0)
        self.right_panel.pack_propagate(False)

        # Scrollable settings
        self.settings_scroll = ctk.CTkScrollableFrame(
            self.right_panel, corner_radius=0
        )
        self.settings_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_settings_panel()

        # ── Bottom: Progress Bar ──────────────────────────────────────
        self.progress_frame = ctk.CTkFrame(self, height=48, corner_radius=0)
        self.progress_frame.pack(fill="x", padx=0, pady=0)
        self.progress_frame.pack_propagate(False)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.progress_label.pack(side="left", padx=(16, 8), pady=4)

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=300,
            height=16,
        )
        self.progress_bar.pack(side="left", padx=8, pady=4)
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa",
        )
        self.status_label.pack(side="right", padx=16, pady=4)

    # ── Settings Panel ────────────────────────────────────────────────────

    def _build_settings_panel(self):
        """Build the settings/configuration panel."""
        scroll = self.settings_scroll

        # ── Output Settings ──
        self._add_section_header(scroll, "📄  Output")

        self.dpi_var = ctk.IntVar(value=300)
        self._add_setting_row(
            scroll, "DPI:", ctk.CTkOptionMenu,
            variable=self.dpi_var,
            values=["150", "200", "300", "400", "600"],
            width=100,
        )

        self.pdf_format_var = ctk.StringVar(value="Image PDF")
        self._add_setting_row(
            scroll, "Format:", ctk.CTkOptionMenu,
            variable=self.pdf_format_var,
            values=["Searchable PDF", "Image PDF", "Images only"],
            width=140,
        )

        # ── Processing Settings ──
        self._add_section_header(scroll, "⚙️  Processing")

        self.page_detection_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Page Detection:", ctk.CTkSwitch,
            variable=self.page_detection_var, onvalue=True, offvalue=False,
            text="",
        )
        # Info label
        ctk.CTkLabel(
            scroll,
            text="Finds paper edges and crops out background",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
        ).pack(fill="x", padx=12, pady=(0, 4), anchor="w")

        self.perspective_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Perspective correction:", ctk.CTkSwitch,
            variable=self.perspective_var, onvalue=True, offvalue=False,
            text="",
        )

        self.deskew_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Deskew:", ctk.CTkSwitch,
            variable=self.deskew_var, onvalue=True, offvalue=False,
            text="",
        )

        self.shadow_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Shadow removal:", ctk.CTkSwitch,
            variable=self.shadow_var, onvalue=True, offvalue=False,
            text="",
        )

        self.whiten_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Whiten background:", ctk.CTkSwitch,
            variable=self.whiten_var, onvalue=True, offvalue=False,
            text="",
        )

        self.contrast_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Enhance contrast:", ctk.CTkSwitch,
            variable=self.contrast_var, onvalue=True, offvalue=False,
            text="",
        )

        self.denoise_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Denoise:", ctk.CTkSwitch,
            variable=self.denoise_var, onvalue=True, offvalue=False,
            text="",
        )

        self.sharpen_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Sharpen:", ctk.CTkSwitch,
            variable=self.sharpen_var, onvalue=True, offvalue=False,
            text="",
        )

        self.normalize_var = ctk.BooleanVar(value=True)
        self._add_setting_row(
            scroll, "Normalize to A4:", ctk.CTkSwitch,
            variable=self.normalize_var, onvalue=True, offvalue=False,
            text="",
        )

        # ── OCR Settings ──
        self._add_section_header(scroll, "🔎  OCR")

        # OCR status indicator
        ocr_status_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        ocr_status_frame.pack(fill="x", padx=12, pady=2)

        ocr_status_label = ctk.CTkLabel(
            ocr_status_frame,
            text=_OCR_MESSAGE,
            font=ctk.CTkFont(size=10),
            text_color="#4CAF50" if _OCR_AVAILABLE else "#FF9800",
            wraplength=240,
            justify="left",
        )
        ocr_status_label.pack(anchor="w")

        self.ocr_var = ctk.BooleanVar(value=_OCR_AVAILABLE)
        self._add_setting_row(
            scroll, "Enable OCR:", ctk.CTkSwitch,
            variable=self.ocr_var, onvalue=True, offvalue=False,
            text="",
        )

        self.ocr_lang_var = ctk.StringVar(value="en")
        self._add_setting_row(
            scroll, "Language:", ctk.CTkOptionMenu,
            variable=self.ocr_lang_var,
            values=["en", "ch", "fr", "de", "es", "pt", "ar", "ja", "ko"],
            width=80,
        )

        # ── Process Button ──
        process_btn = ctk.CTkButton(
            scroll,
            text="▶  PROCESS ALL",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._start_processing,
            fg_color="#2d7d46",
            hover_color="#236b3a",
        )
        process_btn.pack(fill="x", padx=12, pady=(16, 8))

    def _add_section_header(self, parent, text: str):
        """Add a section header label."""
        header = ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=12, pady=(12, 4))

    def _add_setting_row(self, parent, label: str, widget_cls, **kwargs):
        """Add a labeled setting row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12)).pack(
            side="left"
        )

        widget = widget_cls(frame, **kwargs)
        widget.pack(side="right")

    # ── File Operations ───────────────────────────────────────────────────

    def _add_files(self):
        """Open file dialog to add image files."""
        files = filedialog.askopenfilenames(
            title="Select Document Images",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.tiff *.tif *.bmp"),
                ("All Files", "*.*"),
            ],
        )
        if files:
            new_files = [f for f in files if f not in self.input_files]
            self.input_files.extend(new_files)
            self._refresh_file_list()
            if self.input_files:
                self.current_image_index = 0
                self._display_current_image()

    def _add_folder(self):
        """Open folder dialog to add all images from a folder."""
        folder = filedialog.askdirectory(title="Select Folder with Document Images")
        if folder:
            new_files = sorted([
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(SUPPORTED_FORMATS)
            ])
            new_files = [f for f in new_files if f not in self.input_files]
            if new_files:
                self.input_files.extend(new_files)
                self._refresh_file_list()
                if not self.processed_images:
                    self.current_image_index = 0
                    self._display_current_image()

    def _clear_all(self):
        """Clear all loaded files and processed results."""
        self.input_files.clear()
        self.processed_images.clear()
        self.current_image_index = 0
        self._refresh_file_list()
        self._clear_preview()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready")
        self.status_label.configure(text="")
        self.page_label.configure(text="No image")

    def _refresh_file_list(self):
        """Refresh the file listbox."""
        self.file_listbox.delete(0, "end")
        for f in self.input_files:
            self.file_listbox.insert("end", os.path.basename(f))

        self.file_count_label.configure(
            text=f"{len(self.input_files)} file{'s' if len(self.input_files) != 1 else ''} loaded"
        )

        if self.input_files:
            self.file_listbox.selection_set(0)

    # ── Preview ──────────────────────────────────────────────────────────

    def _display_current_image(self):
        """Display the current image (before or after) in the canvas."""
        if not self.input_files:
            self._clear_preview()
            return

        idx = self.current_image_index
        if idx < 0 or idx >= len(self.input_files):
            return

        self.page_label.configure(text=f"Page {idx + 1} of {len(self.input_files)}")

        # Determine navigation state
        self.prev_btn.configure(state="normal" if idx > 0 else "disabled")
        self.next_btn.configure(state="normal" if idx < len(self.input_files) - 1 else "disabled")

        # Show "before" or "after" image
        view = self.view_var.get()

        if view == "After" and idx < len(self.processed_images):
            img_bgr = self.processed_images[idx]
            label_text = "After"
        else:
            img_bgr = cv2.imread(self.input_files[idx])
            label_text = "Before" if view == "Before" else "Before (not processed)"

        if img_bgr is None:
            self._clear_preview()
            return

        # Resize to fit canvas
        self._show_image_on_canvas(img_bgr)

    def _show_image_on_canvas(self, img_bgr: np.ndarray):
        """Resize and display an image on the preview canvas."""
        canvas_w = self.preview_canvas.winfo_width() or 600
        canvas_h = self.preview_canvas.winfo_height() or 400

        if canvas_w < 10 or canvas_h < 10:
            canvas_w, canvas_h = 600, 400

        # Convert and resize
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Maintain aspect ratio
        img_w, img_h = pil_img.size
        scale = min(canvas_w / img_w, canvas_h / img_h, 1.5)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

        # Center on canvas
        x_offset = (canvas_w - new_w) // 2
        y_offset = (canvas_h - new_h) // 2

        self._tk_img = ImageTk.PhotoImage(pil_img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            x_offset, y_offset, anchor="nw", image=self._tk_img
        )

    def _clear_preview(self):
        """Clear the preview canvas."""
        self.preview_canvas.delete("all")
        self.page_label.configure(text="No image")
        self.prev_btn.configure(state="disabled")
        self.next_btn.configure(state="disabled")

    def _on_file_select(self, event):
        """Handle file listbox selection."""
        selection = self.file_listbox.curselection()
        if selection:
            self.current_image_index = selection[0]
            self._display_current_image()

    def _prev_image(self):
        """Show the previous image."""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.file_listbox.selection_clear(0, "end")
            self.file_listbox.selection_set(self.current_image_index)
            self._display_current_image()

    def _next_image(self):
        """Show the next image."""
        if self.current_image_index < len(self.input_files) - 1:
            self.current_image_index += 1
            self.file_listbox.selection_clear(0, "end")
            self.file_listbox.selection_set(self.current_image_index)
            self._display_current_image()

    def _on_view_toggle(self, value):
        """Handle before/after view toggle."""
        self._display_current_image()

    # ── Processing ────────────────────────────────────────────────────────

    def _get_pipeline_config(self) -> PipelineConfig:
        """Build a PipelineConfig from current UI settings."""
        return PipelineConfig(
            dpi=self.dpi_var.get(),
            page_detection=self.page_detection_var.get(),
            perspective_correction=self.perspective_var.get(),
            deskew_enabled=self.deskew_var.get(),
            shadow_removal_enabled=self.shadow_var.get(),
            whiten_enabled=self.whiten_var.get(),
            contrast_enabled=self.contrast_var.get(),
            denoise_enabled=self.denoise_var.get(),
            sharpen_enabled=self.sharpen_var.get(),
            normalize_a4=self.normalize_var.get(),
            ocr_enabled=self.ocr_var.get(),
            ocr_language=self.ocr_lang_var.get(),
            progress_callback=self._on_pipeline_progress,
        )

    def _start_processing(self):
        """Start processing all loaded images."""
        if not self.input_files:
            self.progress_label.configure(text="No files to process!")
            return

        if self.is_processing:
            return

        # Check OCR availability
        wants_ocr = "searchable" in self.pdf_format_var.get().lower()
        if wants_ocr and not _OCR_AVAILABLE:
            # Show a popup warning but still allow processing (with fallback)
            popup = ctk.CTkToplevel(self)
            popup.title("OCR Not Available")
            popup.geometry("480x320")
            popup.transient(self)
            popup.grab_set()

            # Center on parent
            popup.update_idletasks()
            px = self.winfo_x() + (self.winfo_width() - 480) // 2
            py = self.winfo_y() + (self.winfo_height() - 320) // 2
            popup.geometry(f"+{px}+{py}")

            ctk.CTkLabel(
                popup,
                text="⚠️  OCR Engine Not Found",
                font=ctk.CTkFont(size=16, weight="bold"),
            ).pack(padx=20, pady=(20, 10))

            msg = ctk.CTkTextbox(popup, height=160, wrap="word", font=ctk.CTkFont(size=12))
            msg.pack(fill="both", expand=True, padx=20, pady=10)
            msg.insert("end", _OCR_MESSAGE + "\n\n")
            msg.insert("end", (
                "The file will be saved as an Image PDF instead "
                "(same great restoration quality, just without the "
                "searchable text layer).\n\n"
                "Proceeding with Image PDF export..."
            ))
            msg.configure(state="disabled")

            def close_and_proceed():
                popup.destroy()
                self.pdf_format_var.set("Image PDF")
                self._start_processing_impl()

            ctk.CTkButton(
                popup, text="OK, Proceed with Image PDF",
                command=close_and_proceed,
                fg_color="#FF9800", hover_color="#E68900",
            ).pack(padx=20, pady=(10, 20))
            return

        self._start_processing_impl()

    def _start_processing_impl(self):
        """Internal: start processing (after any OCR checks)."""
        self.is_processing = True
        self.progress_label.configure(text="Processing...")
        self.progress_bar.set(0)

        # Run in background thread
        thread = threading.Thread(target=self._process_thread, daemon=True)
        thread.start()

    def _process_thread(self):
        """Background processing thread."""
        try:
            config = self._get_pipeline_config()
            config.output_format = "searchable_pdf" if "searchable" in self.pdf_format_var.get().lower() else "pdf"

            # If OCR is enabled but not available, disable it
            if config.ocr_enabled and not _OCR_AVAILABLE:
                config.ocr_enabled = False
                config.output_format = "pdf"

            processor = BatchProcessor(config=config)
            processor.set_progress_callback(self._on_batch_progress)

            result = processor.process_files(self.input_files, "output.pdf")

            self.after(0, lambda: self._on_processing_complete(result))
        except Exception as e:
            self.after(0, lambda: self._on_processing_error(str(e)))

    def _on_pipeline_progress(self, step: PipelineStep, pct: float):
        """Called during single-image pipeline processing."""
        self.after(0, lambda: self.progress_bar.set(pct))

    def _on_batch_progress(self, step: str, pct: float, current: int, total: int):
        """Called during batch processing."""
        self.after(0, lambda: self.progress_bar.set(pct))
        self.after(0, lambda: self.progress_label.configure(
            text=f"Processing file {current + 1}/{total}..."
        ))
        self.after(0, lambda: self.status_label.configure(text=f"Step: {step}"))

    def _on_processing_complete(self, result: BatchResult):
        """Handle successful processing completion."""
        self.is_processing = False
        self.progress_bar.set(1.0)

        # Load processed images for preview
        self.processed_images.clear()
        for f in self.input_files:
            img = cv2.imread(f)
            if img is not None:
                self.processed_images.append(img)

        msg = (
            f"✅ Done! {result.succeeded}/{result.total} pages processed."
        )
        if result.failed > 0:
            msg += f" {result.failed} failed."

        self.progress_label.configure(text=msg)

        # Show what was created
        output_note = f"Output: {os.path.basename(result.output_path)}"
        # Check if OCR was requested but unavailable
        wants_ocr = "searchable" in self.pdf_format_var.get().lower()
        if wants_ocr and not _OCR_AVAILABLE:
            output_note += " (Image PDF — OCR not installed)"
        self.status_label.configure(text=output_note)

        # Switch to "After" view
        self.view_var.set("After")
        self._display_current_image()

    def _on_processing_error(self, error_msg: str):
        """Handle processing error."""
        self.is_processing = False
        self.progress_label.configure(text=f"❌ Error: {error_msg}")
        self.progress_bar.set(0)

    # ── Export ────────────────────────────────────────────────────────────

    def _export_pdf(self):
        """Export processed images as PDF."""
        if not self.input_files:
            self.progress_label.configure(text="No files to export!")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="SandaScan_Restored.pdf",
        )

        if not output_path:
            return

        self.progress_label.configure(text="Exporting PDF...")
        self.progress_bar.set(0)

        thread = threading.Thread(
            target=self._export_thread, args=(output_path,), daemon=True
        )
        thread.start()

    def _export_thread(self, output_path: str):
        """Background export thread."""
        try:
            from ..core.pipeline import restore_batch

            config = self._get_pipeline_config()

            # Load all images
            images = []
            for f in self.input_files:
                img = cv2.imread(f)
                if img is not None:
                    images.append(img)

            if not images:
                raise ValueError("No valid images to export")

            final_path = restore_batch(images, output_path, config)

            self.after(0, lambda: self.progress_label.configure(
                text=f"✅ Exported: {os.path.basename(final_path)}"
            ))
            self.after(0, lambda: self.progress_bar.set(1.0))

        except Exception as e:
            self.after(0, lambda: self._on_processing_error(str(e)))

    # ── Theme ─────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        """Toggle between dark and light mode."""
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.theme_btn.configure(text="🌙" if new_mode == "Dark" else "☀️")

    # ── About / Help / FAQ Dialogs ───────────────────────────────────────

    def _show_about(self):
        """Show the About dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"About {APP_NAME}")
        dialog.geometry("500x480")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Center on parent
        dialog.update_idletasks()
        px = self.winfo_x() + (self.winfo_width() - 500) // 2
        py = self.winfo_y() + (self.winfo_height() - 480) // 2
        dialog.geometry(f"+{px}+{py}")

        # Logo
        _logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sandascan_logo.png")
        if os.path.exists(_logo_path):
            logo_img = ctk.CTkImage(Image.open(_logo_path), size=(120, 120))
            ctk.CTkLabel(dialog, image=logo_img, text="").pack(pady=(20, 5))

        ctk.CTkLabel(
            dialog,
            text=f"{APP_NAME} v{APP_VERSION}",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(5, 5))

        ctk.CTkLabel(
            dialog,
            text="Document Restoration Suite",
            font=ctk.CTkFont(size=14),
            text_color="#888888",
        ).pack()

        ctk.CTkFrame(dialog, height=1, fg_color="#555555").pack(fill="x", padx=40, pady=15)

        about_text = ctk.CTkTextbox(dialog, height=180, wrap="word", font=ctk.CTkFont(size=12))
        about_text.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        about_text.insert("end", (
            "SandaScan transforms phone photos of documents into "
            "scanner-quality, OCR-ready, searchable PDFs — completely offline.\n\n"
            "Unlike AI image generation tools, SandaScan preserves every pixel "
            "faithfully using computer vision techniques. It never rewrites, "
            "invents, or summarizes text.\n\n"
            "Built with Python, OpenCV, NumPy, Pillow, ReportLab & CustomTkinter.\n\n"
            "SandaScan is developed and published by Bishop Dr. David Sanda (SandaApps).\n"
            "Open source under the MIT Licence.\n\n"
            "Provided totally free for students, lecturers, editors and researchers "
            "alike, for the glory of Jesus and the advancement of academic research.\n\n"
            "© 2026 David Sanda. All rights reserved."
        ))
        about_text.configure(state="disabled")

        ctk.CTkButton(dialog, text="Close", command=dialog.destroy, width=100).pack(pady=(0, 20))

    def _show_help(self):
        """Show the Help dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{APP_NAME} Help")
        dialog.geometry("580x520")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        px = self.winfo_x() + (self.winfo_width() - 580) // 2
        py = self.winfo_y() + (self.winfo_height() - 520) // 2
        dialog.geometry(f"+{px}+{py}")

        ctk.CTkLabel(
            dialog,
            text=f"📖  {APP_NAME} — Help Guide",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(padx=25, pady=(20, 10))

        ctk.CTkFrame(dialog, height=1, fg_color="#555555").pack(fill="x", padx=25, pady=5)

        # Help content with sections
        sections = [
            ("📂  Getting Started",
             "1. Click 'Add Files' or 'Add Folder' to load document photos\n"
             "2. Select your output format (Image PDF or Searchable PDF)\n"
             "3. Toggle processing features on/off as needed\n"
             "4. Click 'Process All' to start restoration\n"
             "5. Use 'Export PDF' to save the result"),
            ("⚙️  Processing Features",
             "• Page Detection — Finds paper edges and crops background\n"
             "• Perspective Correction — Straightens angled pages\n"
             "• Shadow Removal — Eliminates phone/hand shadows\n"
             "• Background Whitening — Makes paper look freshly scanned\n"
             "• Contrast Enhancement — Improves text readability\n"
             "• Denoise — Removes camera noise and JPEG artifacts\n"
             "• Adaptive Sharpening — Sharpens text without noise"),
            ("⌨️  Keyboard Shortcuts",
             "Ctrl+O — Add Files\n"
             "Ctrl+F — Add Folder\n"
             "Ctrl+P — Process All\n"
             "Ctrl+S — Export PDF\n"
             "Ctrl+R — Clear All\n"
             "Esc — Clear All"),
            ("🔎  Searchable PDF (OCR)",
             "Searchable PDFs require Tesseract OCR to be installed.\n"
             "Download from: https://github.com/UB-Mannheim/tesseract/wiki\n"
             "Then run: pip install pytesseract\n\n"
             "Without OCR, the app exports standard Image PDFs."),
        ]

        help_text = ctk.CTkTextbox(dialog, height=320, wrap="word", font=ctk.CTkFont(size=12))
        help_text.pack(fill="both", expand=True, padx=25, pady=(10, 15))

        for title, body in sections:
            help_text.insert("end", f"{title}\n", ("bold",))
            help_text.insert("end", f"{body}\n\n")
            help_text.tag_config("bold", font=ctk.CTkFont(size=12, weight="bold"))

        help_text.configure(state="disabled")

        ctk.CTkButton(dialog, text="Close", command=dialog.destroy, width=100).pack(pady=(0, 20))

    def _show_faq(self):
        """Show the FAQ dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{APP_NAME} — FAQ")
        dialog.geometry("580x520")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        px = self.winfo_x() + (self.winfo_width() - 580) // 2
        py = self.winfo_y() + (self.winfo_height() - 520) // 2
        dialog.geometry(f"+{px}+{py}")

        ctk.CTkLabel(
            dialog,
            text=f"❓  {APP_NAME} — Frequently Asked Questions",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=25, pady=(20, 10))

        ctk.CTkFrame(dialog, height=1, fg_color="#555555").pack(fill="x", padx=25, pady=5)

        faqs = [
            ("Q: Does SandaScan work without an internet connection?",
             "Yes! SandaScan runs completely offline. No data ever leaves your computer."),
            ("Q: Why is my searchable PDF not searchable?",
             "You need Tesseract OCR installed. Download from "
             "github.com/UB-Mannheim/tesseract/wiki, then run: pip install pytesseract"),
            ("Q: Can I process multiple pages at once?",
             "Yes. Add all your images (or an entire folder), then click Process All. "
             "They will be merged into a single multi-page PDF."),
            ("Q: What image formats are supported?",
             "JPG, JPEG, PNG, TIFF, TIF, and BMP."),
            ("Q: Will SandaScan alter my original images?",
             "No. Your original files are never modified. The app creates new PDF output."),
            ("Q: Does SandaScan use AI to generate or rewrite text?",
             "No. SandaScan uses computer vision (not AI generation). It preserves "
             "every pixel faithfully — it never rewrites, invents, or summarizes text."),
            ("Q: What DPI should I use?",
             "300 DPI is recommended for most uses. Use 600 DPI for archival/master copies."),
            ("Q: Is SandaScan free?",
             "Yes. SandaScan is open-source under the MIT License."),
        ]

        faq_text = ctk.CTkTextbox(dialog, height=330, wrap="word", font=ctk.CTkFont(size=12))
        faq_text.pack(fill="both", expand=True, padx=25, pady=(10, 15))

        for i, (q, a) in enumerate(faqs):
            faq_text.insert("end", f"{q}\n", ("q",))
            faq_text.insert("end", f"{a}\n\n", ("a",))
            faq_text.tag_config("q", font=ctk.CTkFont(size=12, weight="bold"))
            faq_text.tag_config("a", font=ctk.CTkFont(size=11), foreground="#BBBBBB")

        faq_text.configure(state="disabled")

        ctk.CTkButton(dialog, text="Close", command=dialog.destroy, width=100).pack(pady=(0, 20))

    # ── Utilities ─────────────────────────────────────────────────────────

    def _on_close(self):
        """Clean up on close."""
        self.quit()
        self.destroy()
