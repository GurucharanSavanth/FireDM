@echo off
setlocal

cd /d "%~dp0"

echo Building FireDM Windows release package...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows-build.ps1" -Release
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Release build completed. Open the release folder for GitHub upload assets.
) else (
    echo Release build failed with exit code %EXIT_CODE%.
)

echo.
pause
exit /b %EXIT_CODE%
