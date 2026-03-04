@echo off
REM Setup Windows Task Scheduler for Weekly CEO Briefing
REM This creates a task that runs every Monday at 8:00 AM

echo ============================================================
echo Weekly CEO Briefing - Task Scheduler Setup
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires administrator privileges.
    echo.
    echo Please:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running with administrator privileges
echo.

REM Get paths
set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\app\.venv\Scripts\python.exe"
set "TRIGGER_SCRIPT=%PROJECT_DIR%\app\scripts\weekly_briefing_trigger.py"

echo Project Directory: %PROJECT_DIR%
echo Python Executable: %PYTHON_EXE%
echo Trigger Script: %TRIGGER_SCRIPT%
echo.

REM Verify files exist
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at:
    echo   %PYTHON_EXE%
    echo.
    echo Please ensure the virtual environment is set up correctly.
    pause
    exit /b 1
)

if not exist "%TRIGGER_SCRIPT%" (
    echo [ERROR] Trigger script not found at:
    echo   %TRIGGER_SCRIPT%
    echo.
    pause
    exit /b 1
)

echo [OK] All required files found
echo.

REM Delete existing task if it exists
echo [STEP 1] Checking for existing task...
schtasks /query /tn "WeeklyCEOBriefing" >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Found existing task, deleting...
    schtasks /delete /tn "WeeklyCEOBriefing" /f >nul 2>&1
    echo [OK] Deleted existing task
) else (
    echo [OK] No existing task found
)
echo.

REM Create the scheduled task
echo [STEP 2] Creating scheduled task...
echo.

schtasks /create ^
    /tn "WeeklyCEOBriefing" ^
    /tr "\"%PYTHON_EXE%\" \"%TRIGGER_SCRIPT%\"" ^
    /sc weekly ^
    /d MON ^
    /st 08:00 ^
    /rl HIGHEST ^
    /f

if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo [SUCCESS] Scheduled task created successfully!
    echo ============================================================
    echo.
    echo Task Details:
    echo   Name: WeeklyCEOBriefing
    echo   Schedule: Every Monday at 8:00 AM
    echo   Action: Run Python trigger script
    echo   Script: %TRIGGER_SCRIPT%
    echo.
    echo ============================================================
    echo Next Steps:
    echo ============================================================
    echo.
    echo 1. Verify the task:
    echo    schtasks /query /tn "WeeklyCEOBriefing" /v /fo list
    echo.
    echo 2. Test manually (will run on next Monday at 8 AM):
    echo    schtasks /run /tn "WeeklyCEOBriefing"
    echo.
    echo 3. View task in Task Scheduler GUI:
    echo    - Press Win+R
    echo    - Type: taskschd.msc
    echo    - Look for "WeeklyCEOBriefing"
    echo.
    echo 4. To delete the task:
    echo    schtasks /delete /tn "WeeklyCEOBriefing" /f
    echo.
    echo ============================================================
    echo IMPORTANT NOTE:
    echo ============================================================
    echo.
    echo The task will run automatically every Monday at 8 AM.
    echo It will call Claude Code to generate the briefing.
    echo.
    echo You can test it manually by running:
    echo   schtasks /run /tn "WeeklyCEOBriefing"
    echo.
    echo But note: This will only work when Claude Code is NOT already running.
    echo.
) else (
    echo.
    echo ============================================================
    echo [ERROR] Failed to create scheduled task
    echo ============================================================
    echo.
    echo Troubleshooting:
    echo   1. Make sure you ran this as Administrator
    echo   2. Check that Python path is correct
    echo   3. Check that trigger script exists
    echo.
)

pause