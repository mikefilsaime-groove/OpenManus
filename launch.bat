@echo off
echo OpenManus Web Interface Launcher
echo ==============================

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run setup first.
    pause
    exit /b 1
)

REM Check if config.toml exists
if not exist "config\config.toml" (
    echo Config file not found. Creating from example...
    copy config\config.example.toml config\config.toml
    echo Please edit config\config.toml to add your API keys.
    pause
    exit /b 1
)

REM Launch the web interface
python run_web.py
pause
