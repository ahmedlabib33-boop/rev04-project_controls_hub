@echo off
echo Project Controls Intelligence Hub - No-Git Sync
echo.
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: RUN_FULL_PROJECT_NO_GIT_SYNC.bat [Watch^|Once^|DryRun] [interval_seconds]
    echo.
    echo Modes:
    echo   Watch  - Continuous sync with interval
    echo   Once   - Single sync operation
    echo   DryRun - Simulate sync without uploading
    exit /b 1
)

set MODE=%~1
set INTERVAL=%~2
if "%~2"=="" set INTERVAL=30

powershell -ExecutionPolicy Bypass -File "tools\github_no_git_sync.ps1" -Mode %MODE% -Interval %INTERVAL%
