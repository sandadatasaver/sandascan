"""
SandaScan entry point — run with: python -m SandaScan

Must be run from the PROJECT ROOT directory (the folder containing SandaScan/),
not from inside the SandaScan/ package itself.

Example:
    cd SandaScan_v1.0/
    python -m SandaScan
"""

import sys
import os

# Ensure the parent directory is on sys.path so relative imports work
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_pkg_dir)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from SandaScan.gui.main_window import SandaScanApp


def main():
    """Launch the SandaScan application."""
    app = SandaScanApp()
    app.mainloop()


if __name__ == "__main__":
    main()
