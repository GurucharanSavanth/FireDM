@echo off
setlocal

cd /d "%~dp0"

set "CHANNEL=%~1"
set "EXTRA_ARGS="
if "%CHANNEL%"=="" (
    set "CHANNEL=dev"
) else (
    if "%CHANNEL:~0,2%"=="--" (
        set "CHANNEL=dev"
    ) else (
        shift /1
    )
)

:collect_args
if "%~1"=="" goto args_done
set "EXTRA_ARGS=%EXTRA_ARGS% %1"
shift /1
goto collect_args

:args_done

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python not found. Create .venv or put python on PATH.
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

echo Building FireDM Windows installer release...
echo Channel: %CHANNEL%
"%PYTHON_EXE%" "%~dp0scripts\release\build_windows.py" --arch x64 --channel "%CHANNEL%" %EXTRA_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Release build completed.
    echo Installer assets are under dist\installers, dist\portable, dist\checksums, and dist\release-manifest.json.
) else (
    echo Release build failed with exit code %EXIT_CODE%.
)

echo.
if not "%FIREDM_NO_PAUSE%"=="1" pause
exit /b %EXIT_CODE%
