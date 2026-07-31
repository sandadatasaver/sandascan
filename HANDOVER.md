# 📄 SANDA SCAN — PROJECT HANDOVER NOTE
**Version:** 1.0.1 | **Date:** July 30, 2026
**Developer:** Bishop Dr. David Sanda (SandaApps)
**GitHub:** https://github.com/sandadatasaver/sandascan
**Website:** https://davidsanda.com/sandascan

---

## 📋 PROJECT OVERVIEW

SandaScan is a professional-grade desktop document restoration application that transforms phone photos of documents into scanner-quality, OCR-ready, searchable PDFs — completely offline. It uses computer vision (not AI generation) to preserve every pixel faithfully.

---

## 🌐 ONLINE PRESENCE

| Property | URL |
|---|---|
| **GitHub Repo** | https://github.com/sandadatasaver/sandascan |
| **Website** | https://davidsanda.com/sandascan |
| **Author Site** | https://davidsanda.com |

---

## 🏗️ PROJECT STRUCTURE

```
sandascan/
├── run.py                          # Entry: python run.py
├── app.py                          # Entry: python app.py
├── Run_SandaScan.bat               # Windows double-click launcher
├── Run_Diagnostic.bat              # Windows diagnostics
├── diagnose.py                     # Diagnostic tool
├── requirements.txt                # Python dependencies
├── SandaScan_installer.iss         # Inno Setup script for Windows installer
├── SandaScan.spec                  # PyInstaller build spec
├── build_exe.bat                   # Windows build helper
├── LICENSE                         # MIT License
├── README.md                       # Documentation
├── .gitignore
├── .github/workflows/build.yml     # Cross-platform CI/CD (Win/Mac/Linux)
│
├── SandaScan/                      # Main Python package
│   ├── __init__.py                 # Package metadata
│   ├── __main__.py                 # python -m SandaScan
│   ├── core/                       # Computer vision engine
│   │   ├── pipeline.py             # Restoration orchestrator
│   │   ├── perspective.py          # Page detection + perspective correction
│   │   ├── shadows.py              # Shadow removal
│   │   ├── enhance.py              # Background whitening + contrast
│   │   ├── sharpen.py              # Adaptive sharpening
│   │   ├── noise.py                # Denoising
│   │   ├── crop.py                 # A4 normalization
│   │   ├── pdf.py                  # PDF generation (ReportLab)
│   │   ├── ocr.py                  # OCR (pytesseract / tesserocr)
│   │   └── batch.py                # Batch processing
│   ├── gui/
│   │   └── main_window.py          # CustomTkinter GUI (1100×700)
│   └── assets/
│       ├── sandascan_logo.png      # Full logo
│       ├── sandascan_icon.png      # App icon (PNG)
│       └── sandascan_app_icon.ico  # App icon (Windows ICO)
│
└── website/                        # One-page website source
    ├── index.html                  # Green/black themed landing page
    ├── sandascan_logo.png
    ├── favicon.ico
    ├── favicon-16x16.png
    ├── favicon-32x32.png
    └── android-chrome-192x192.png
```

---

## 🔧 KEY FILES & WHAT THEY DO

### Core Processing Pipeline
| File | Purpose | Key Functions |
|---|---|---|
| `perspective.py` | Page detection (5 strategies), perspective correction, deskew | `find_document_contour()`, `correct_perspective()`, `deskew()` |
| `shadows.py` | Shadow removal via morphological closing | `remove_shadows()` |
| `enhance.py` | Background whitening, CLAHE contrast, auto levels | `whiten_background()`, `enhance_contrast()` |
| `sharpen.py` | Adaptive edge-aware unsharp masking | `adaptive_sharpen()` |
| `noise.py` | Non-Local Means denoising, dust removal | `denoise()` |
| `pipeline.py` | Orchestrates all steps with error handling per-page | `restore_document()`, `restore_batch()` |
| `ocr.py` | Text extraction (pytesseract primary, tesserocr fallback) | `extract_text()`, `make_searchable_pdf()` |
| `pdf.py` | Image PDF + searchable PDF with invisible text layer | `images_to_pdf()`, `images_to_searchable_pdf()` |

### GUI
| File | Purpose |
|---|---|
| `main_window.py` | Full CustomTkinter app: menu bar, 3-panel layout, settings, About/Help/FAQ dialogs |

---

## 🛠️ BUILD INSTRUCTIONS

### For development (run from source)
```bash
pip install -r requirements.txt
python run.py
```

### For Windows .exe (single-file)
```batch
pyinstaller --onefile --windowed --name "SandaScan.exe" ^
  --icon "SandaScan\assets\sandascan_app_icon.ico" ^
  --add-data "SandaScan\core;SandaScan\core" ^
  --add-data "SandaScan\gui;SandaScan\gui" ^
  --add-data "SandaScan\assets;SandaScan\assets" ^
  --hidden-import PIL._tkinter_finder ^
  run.py
```

### For Windows Installer
1. Build the .exe first (command above)
2. Right-click `SandaScan_installer.iss` → Compile (requires Inno Setup)
3. Output: `installer\SandaScan_v1.0.1_Setup.exe`

### For cross-platform (via GitHub Actions)
Push a tag: `git tag v1.0.1 && git push origin v1.0.1`
Or trigger manually from GitHub Actions tab → "Build & Release" → Run workflow

Builds for: Windows (.exe), macOS (.app/.dmg), Linux (.AppImage)

---

## 🔐 DEPENDENCIES

### Required (core restoration works without Tesseract)
- opencv-python, numpy, Pillow, reportlab, customtkinter

### Optional (for Searchable PDFs)
- Tesseract OCR binary: https://github.com/UB-Mannheim/tesseract/wiki
- pytesseract: `pip install pytesseract`

---

## 🧪 TESTING NOTES

- Page detection uses 5 strategies in sequence (Canny → Adaptive → OTSU → Convex Hull → Frame Edge)
- Failed pages get a safe fallback (resize to A4 with white padding, no distortion)
- OCR per-page: if some pages fail OCR, they get blank text layers while others succeed
- The app detects Tesseract at startup and searches common install paths

---

## 🌐 WEBSITE DEPLOYMENT

Upload the `website/` folder contents to:
```
https://davidsanda.com/sandascan/
```

Files to upload:
- `index.html`
- `sandascan_logo.png`
- `favicon.ico`
- `favicon-16x16.png`
- `favicon-32x32.png`
- `android-chrome-192x192.png`

---

## 📦 DELIVERABLES

| Zip File | Contents |
|---|---|
| `SandaScan-GitHub-v1.0.zip` | Full GitHub repo with .git history, website, all source |
| `SandaScan-v1.0.1.zip` | App only (no .git, no website) |
| `sandascan-website.zip` | Website HTML + logo + favicons |

---

## 📝 TO-DO / FUTURE WORK

- [ ] Version 2: Book scanner mode, curved page flattening
- [ ] Version 3: AI-assisted restoration for faded ink (without inventing text)
- [ ] Add drag-and-drop support to the GUI
- [ ] Add multi-language OCR support beyond English
- [ ] Package Tesseract with the installer for one-click setup

---

*Handover prepared by the development environment. For questions, contact the repository maintainer at https://github.com/sandadatasaver*
