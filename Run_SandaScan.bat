@echo off
REM SandaScan — Document Restoration Suite
REM Windows launcher — double-click this file to run
REM
REM ✅ WORKS WITHOUT TESSERACT (restoration + Image PDF):
REM    Perspective correction, shadow removal, background whitening,
REM    sharpening, denoising, auto-crop, Image PDF export
REM
REM ⚠️  SEARCHABLE PDF needs Tesseract OCR (optional add-on):
REM    Install from: https://github.com/UB-Mannheim/tesseract/wiki
REM    Then: pip install pytesseract

title SandaScan — Document Restoration

echo ====================================================
echo   SandaScan — Document Restoration Suite
echo ====================================================
echo.
echo   ✅ Core restoration works WITHOUT Tesseract
echo   ⚠️  Searchable PDF requires OCR (optional extra)
echo.

REM Navigate to the script's directory
cd /d "%~dp0"

REM -------------------------------------------------------
REM Step 1: Check Python
REM -------------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.12+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK]   Python found:
python --version

REM -------------------------------------------------------
REM Step 2: Install/verify Python dependencies
REM -------------------------------------------------------
echo.
echo [INFO] Installing required packages (if not already installed)...
echo        This may take a minute on first run.
echo.

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Some packages could not be installed.
    echo           The app may not start correctly.
    echo.
    echo Try running this command manually:
    echo   pip install -r "%~dp0requirements.txt"
    echo.
    pause
    exit /b 1
)

echo [OK]   All dependencies installed.

REM -------------------------------------------------------
REM Step 3: Launch SandaScan
REM -------------------------------------------------------
echo.
echo ====================================================
echo   Launching SandaScan...
echo ====================================================
echo.
echo   ✅ The app window should open now.
echo   ✅ Close this window after you're done, or
echo      close the app first, then press any key here.
echo.

python run.py

REM -------------------------------------------------------
REM Step 4: App has exited
REM -------------------------------------------------------
echo.
echo ====================================================
echo   SandaScan has exited.
echo ====================================================
echo.
echo   📄 Your restored files are in the folder where
echo      you added your images.
echo.
echo   💡 Tip: For searchable PDFs, install Tesseract from:
echo      https://github.com/UB-Mannheim/tesseract/wiki
echo      Then: pip install pytesseract
echo.
echo   Press any key to close this window...
pause >nul
