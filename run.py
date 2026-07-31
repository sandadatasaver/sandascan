#!/usr/bin/env python3
"""
SandaScan — Document Restoration Suite
Quick launcher — double-click or run: python run.py

✅ Core restoration (perspective, shadows, whitening, PDF) works
   without any extra software — just pip install the requirements.

⚠️  For Searchable PDFs (OCR text layer), install Tesseract from:
    https://github.com/UB-Mannheim/tesseract/wiki
    Then: pip install pytesseract
"""

import sys
import os
import traceback


def main():
    """Launch the SandaScan application."""
    # Ensure we can find the SandaScan package
    _project_root = os.path.dirname(os.path.abspath(__file__))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

    # Point tessdata to the bundled folder (for tesserocr on Linux/Mac)
    _expected_tessdata = os.path.join(_project_root, "tessdata")
    if os.path.isdir(_expected_tessdata):
        os.environ.setdefault("TESSDATA_PREFIX", _expected_tessdata)

    try:
        from SandaScan.gui.main_window import SandaScanApp
        app = SandaScanApp()
        app.mainloop()
    except ImportError as e:
        missing = str(e)
        print("=" * 60)
        print("  SANDA SCAN — MISSING DEPENDENCIES")
        print("=" * 60)
        print()
        print(f"  Error: {missing}")
        print()
        print("  Run this command to install all required packages:")
        print()
        print(f"    pip install -r \"{os.path.join(_project_root, 'SandaScan', 'requirements.txt')}\"")
        print()
        print("  Then run SandaScan again.")
        print()
        input("  Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print("=" * 60)
        print("  SANDA SCAN — UNEXPECTED ERROR")
        print("=" * 60)
        print()
        traceback.print_exc()
        print()
        input("  Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
