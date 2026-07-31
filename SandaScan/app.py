#!/usr/bin/env python3
"""
SandaScan — Document Restoration Suite

Entry point. Can be run in multiple ways:
    python app.py              # from the SandaScan/ package directory
    python SandaScan/app.py    # from the parent directory
    python -m SandaScan        # from the parent directory
"""

import sys
import os

# ── Fix Import Path ─────────────────────────────────────────────────────
# Add the PARENT directory so 'from SandaScan.gui...' resolves correctly
# whether you run from inside SandaScan/ or from the project root.
_app_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_app_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# ── Launch ──────────────────────────────────────────────────────────────
from SandaScan.gui.main_window import SandaScanApp


def main():
    """Launch the SandaScan application."""
    app = SandaScanApp()
    app.mainloop()


if __name__ == "__main__":
    main()
