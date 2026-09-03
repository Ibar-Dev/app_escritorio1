@echo off
cd /d "%~dp0"
if exist "dist\ZooPicasso\ZooPicasso.exe" (
    start "" "dist\ZooPicasso\ZooPicasso.exe"
) else (
    uv run main.py
    if errorlevel 1 pause
)