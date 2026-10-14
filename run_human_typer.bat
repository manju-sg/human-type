@echo off
title Human Code Typer
cd /d "%~dp0"
echo Starting Human Code Typer GUI...
python run_typer.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Error] Failed to start. Make sure python and dependencies are installed.
    pause
)
