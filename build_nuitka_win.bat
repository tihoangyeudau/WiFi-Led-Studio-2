@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo  Starting WiFi Led Studio Nuitka Build for Windows...
echo ========================================================

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_nuitka_win.ps1" %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed with exit code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Build completed successfully.
pause
