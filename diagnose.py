#!/usr/bin/env python3
"""
SandaScan — Diagnostic Tool
Run this to check why the app isn't launching.
"""

import sys
import os

print("=" * 60)
print("  SANDA SCAN — DIAGNOSTIC REPORT")
print("=" * 60)
print()

# Where are we?
print(f"📁 Current directory:  {os.getcwd()}")
print(f"🐍 Python version:    {sys.version}")
print(f"📂 sys.path[0]:       {sys.path[0] if sys.path else '(empty)'}")
print()

# Check if SandaScan folder exists
here = os.getcwd()
sanda_paths = [
    os.path.join(here, "SandaScan"),
    os.path.join(here, "..", "SandaScan"),
    os.path.join(here, "sandaScan"),
]
found_pkg = False
for p in sanda_paths:
    exists = os.path.isdir(p)
    print(f"{'✅' if exists else '❌'} SandaScan folder at: {p}")
    if exists:
        found_pkg = True

if not found_pkg:
    print("\n❌ ERROR: Cannot find the SandaScan/ folder!")
    print("   Make sure 'SandaScan/' is in the same folder as this script.")
    print()
    print("   Your current folder should contain:")
    print("     ✅ SandaScan/    (the application package)")
    print("     ✅ run.py        (launcher)")
    print("     ✅ Run_SandaScan.bat  (Windows launcher)")
print()

# Check dependencies
print("📦 Checking Python packages:")
packages = [
    ("opencv-python", "cv2", "Image processing"),
    ("numpy", "numpy", "Numerical computing"),
    ("Pillow", "PIL", "Image handling"),
    ("reportlab", "reportlab", "PDF generation"),
    ("customtkinter", "customtkinter", "GUI framework"),
    ("tkinter", "tkinter", "Python GUI (built-in)"),
]

all_ok = True
for pip_name, import_name, desc in packages:
    try:
        __import__(import_name)
        print(f"  ✅ {pip_name:20s}  ({desc})")
    except ImportError as e:
        print(f"  ❌ {pip_name:20s}  ({desc}) — MISSING: {e}")
        all_ok = False

print()

# Try importing SandaScan
print("📦 Testing SandaScan imports:")
try:
    sys.path.insert(0, here)
    from SandaScan.core.pipeline import PipelineConfig
    print("  ✅ SandaScan.core.pipeline")
except Exception as e:
    print(f"  ❌ SandaScan.core.pipeline — {e}")
    all_ok = False

try:
    from SandaScan.core.ocr import get_available_backends
    print(f"  ✅ SandaScan.core.ocr (backends: {get_available_backends()})")
except Exception as e:
    print(f"  ❌ SandaScan.core.ocr — {e}")

try:
    from SandaScan.core.pdf import images_to_pdf
    print("  ✅ SandaScan.core.pdf")
except Exception as e:
    print(f"  ❌ SandaScan.core.pdf — {e}")

try:
    from SandaScan.gui.main_window import SandaScanApp
    print("  ✅ SandaScan.gui.main_window")
except Exception as e:
    print(f"  ❌ SandaScan.gui.main_window — {e}")
    all_ok = False

print()

if all_ok:
    print("🎉 Everything looks good! The app should launch.")
    print("   Try running: python run.py")
else:
    print("⚠️  Some issues found (see ❌ above).")
    print("   Run this to fix: pip install -r SandaScan/requirements.txt")
