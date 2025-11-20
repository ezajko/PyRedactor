@echo off
REM PyRedactor Launcher for Windows
REM This script launches the application using the virtual environment if available.

setlocal
cd /d "%~dp0"

REM Check for virtual environment pythonw (no console window)
if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" -m pyredactor.main
) else (
    REM Check for virtual environment python (with console, fallback)
    if exist "venv\Scripts\python.exe" (
        "venv\Scripts\python.exe" -m pyredactor.main
    ) else (
        echo Virtual environment 'venv' not found.
        echo Please ensure you have followed the installation instructions in README.md
        echo and created a virtual environment named 'venv'.
        echo.
        echo Press any key to try running with global Python...
        pause >nul
        python -m pyredactor.main
    )
)

endlocal
