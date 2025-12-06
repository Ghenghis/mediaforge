@echo off
title MEDIAFORGE - Master Launcher
color 0A

echo.
echo ============================================================
echo   MEDIAFORGE - MASTER LAUNCHER
echo   Complete Story-Driven Image Generation System
echo ============================================================
echo.

:: Check for Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

:: Set working directory
cd /d "%~dp0"

:: Create necessary directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "training" mkdir training

echo [1/6] Starting Core APIs...
start "Rating System API" /min python scripts\rating_system_api.py
timeout /t 2 > nul

start "Country Rating API" /min python scripts\country_rating_api.py
timeout /t 1 > nul

start "Guardrails Engine" /min python scripts\guardrails.py
timeout /t 1 > nul

echo [2/6] Starting Story Engine...
start "Frontier Stories" /min python scripts\frontier_stories_engine.py
timeout /t 2 > nul

start "Story Collection System" /min python scripts\story_collection_system.py
timeout /t 1 > nul

echo [3/6] Starting Learning Systems...
start "AI Learning Brain" /min python scripts\ai_learning_brain.py
timeout /t 1 > nul

start "Advanced Learning" /min python scripts\advanced_learning_system.py
timeout /t 1 > nul

echo [4/6] Starting Dashboard API...
start "Dashboard API" /min python scripts\api\dashboard_api.py
timeout /t 2 > nul

echo [5/6] Starting Automation Services...
start "Playwright Pipeline" /min python scripts\automation\playwright_pipeline.py
timeout /t 1 > nul

start "ComfyUI Integration" /min python scripts\comfyui\comfyui_api.py
timeout /t 1 > nul

echo [6/6] Launching Story Integration Menu...
timeout /t 2 > nul
python scripts\story_integration_menu.py

echo.
echo ============================================================
echo   All services started! Press any key to stop all...
echo ============================================================
pause > nul

:: Kill all Python processes started by this launcher
taskkill /f /im python.exe > nul 2>&1
echo Services stopped.
pause
