@echo off
REM SandaScan — Build Windows Executable
REM Run this on Windows to build a standalone .exe
REM
REM Prerequisites:
REM   1. Python 3.12+ installed
REM   2. All dependencies installed: pip install -r requirements.txt
REM   3. PyInstaller installed: pip install pyinstaller
REM
REM The .exe will be created in the dist/SandaScan/ folder

title Building SandaScan .exe

cd /d "%~dp0"

echo ====================================================
echo   Building SandaScan — Windows Executable
echo ====================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Check PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Installing PyInstaller...
    pip install pyinstaller
)

echo [BUILD] Creating executable...
echo.

pyinstaller SandaScan.spec --clean

if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo   ✅ BUILD SUCCESSFUL!
    echo ====================================================
    echo.
    echo   Your .exe is at:
    echo   dist\SandaScan\SandaScan.exe
    echo.
    echo   To distribute, ZIP the entire dist\SandaScan\ folder
    echo   along with the tessdata\ folder (for OCR).
    echo.
) else (
    echo.
    echo [ERROR] Build failed. Check the output above.
)

pause
