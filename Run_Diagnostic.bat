@echo off
REM SandaScan — Diagnostic Tool
REM Double-click this to check why the app isn't launching

title SandaScan — Diagnostic

cd /d "%~dp0"

echo ====================================================
echo   SandaScan — System Diagnostic
echo ====================================================
echo.
echo This will check Python, dependencies, and imports.
echo.

python diagnose.py

echo.
pause
