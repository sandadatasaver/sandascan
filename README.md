# 📄 SandaScan — Document Restoration Suite

**Transform phone photos into scanner-quality, OCR-ready PDFs — completely offline.**

SandaScan is a professional-grade desktop application that uses computer vision to restore document photos. Unlike AI "regeneration" tools, SandaScan preserves **every pixel faithfully** — never rewriting, inventing, or summarizing text.

---

## ✨ Features

| Feature | Description | Requires Tesseract? |
|---|---|---|
| 🖼️ **Auto Page Detection** | Automatically finds document edges in photos | ❌ No |
| 🔄 **Perspective Correction** | Straightens angled pages like Adobe Scan | ❌ No |
| 🌓 **Shadow Removal** | Eliminates phone/hand shadows and uneven lighting | ❌ No |
| ⚪ **Background Whitening** | Makes paper look freshly flatbed-scanned | ❌ No |
| 🔍 **Adaptive Sharpening** | Sharpens text without amplifying noise | ❌ No |
| 🧹 **Noise Removal** | Cleans camera noise, JPEG artifacts, dust | ❌ No |
| 📄 **Image PDF Export** | Multi-page A4 PDF at 300/600 DPI | ❌ No |
| 🔎 **Searchable PDF** | OCR text layer for full-text search | ✅ Yes (optional) |
| 📦 **Batch Processing** | Process entire folders in one click | ❌ No |
| 🖥️ **Professional GUI** | Dark mode, preview, progress, keyboard shortcuts | ❌ No |

**Core restoration works 100% without installing anything extra.** Only the Searchable PDF feature needs Tesseract OCR.

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/sandadatasaver/sandascan.git
cd sandascan

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python run.py
```

### Windows Users (double-click to launch)

Just double-click **`Run_SandaScan.bat`**

---

## 🖥️ Usage

1. **Load images** — Click "Add Files" or "Add Folder"
2. **Configure** — Toggle processing steps on/off
3. **Process** — Click "Process All"
4. **Preview** — Toggle Before/After views
5. **Export** — Save as searchable or image PDF

### Keyboard Shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl+O` | Add files |
| `Ctrl+F` | Add folder |
| `Ctrl+P` | Process all |
| `Ctrl+S` | Export PDF |
| `Ctrl+R` | Clear all |

---

## 🏗️ Project Structure

```
sandascan/
├── run.py                  # python run.py
├── app.py                  # python app.py
├── Run_SandaScan.bat       # Double-click to launch (Windows)
├── Run_Diagnostic.bat      # Double-click to diagnose issues
├── diagnose.py             # Diagnostic tool
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── README.md               # This file
├── SandaScan/              # Application package
│   ├── __init__.py
│   ├── __main__.py
│   ├── core/               # Computer vision engine
│   │   ├── pipeline.py     # Restoration orchestrator
│   │   ├── perspective.py  # Page detection & deskew
│   │   ├── shadows.py      # Shadow removal
│   │   ├── enhance.py      # Whitening & contrast
│   │   ├── sharpen.py      # Adaptive sharpening
│   │   ├── noise.py        # Denoising
│   │   ├── crop.py         # A4 normalization
│   │   ├── pdf.py          # PDF generation
│   │   ├── ocr.py          # OCR (pytesseract/tesserocr)
│   │   └── batch.py        # Batch processing
│   └── gui/
│       └── main_window.py  # CustomTkinter GUI
```

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.12+ |
| **Computer Vision** | OpenCV, NumPy |
| **Image Processing** | Pillow |
| **PDF Generation** | ReportLab |
| **GUI** | CustomTkinter |
| **OCR (optional)** | pytesseract |

---

## 📥 Adding OCR (Searchable PDFs)

The app works perfectly without this — you get Image PDFs. For searchable text:

```bash
# 1. Install Tesseract binary
#    Download: https://github.com/UB-Mannheim/tesseract/wiki

# 2. Install Python bridge
pip install pytesseract
```

---

## 🤝 License

MIT License — free to use, modify, and distribute.

Built with ❤️ for archival-quality document restoration.
