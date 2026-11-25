@echo off
rem Double-click to check the Project Reforged patch versions.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check-versions.ps1" %*
echo.
pause
