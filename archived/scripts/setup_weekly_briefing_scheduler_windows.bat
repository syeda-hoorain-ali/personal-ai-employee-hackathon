@echo off
REM Setup Windows Task Scheduler for Weekly CEO Briefing
REM Runs every Monday at 8:00 AM

echo ========================================
echo Weekly CEO Briefing Scheduler Setup
echo ========================================
echo.

REM Get the current directory
set "PROJECT_DIR=%~dp0.."
set "PYTHON_EXE=%PROJECT_DIR%\app\.venv\Scripts\python.exe"
set "TRIGGER_SCRIPT=%PROJECT_DIR%\app\scripts\weekly_briefing_trigger.py"

echo Project Directory: %PROJECT_DIR%
echo Python Executable: %PYTHON_EXE%
echo Trigger Script: %TRIGGER_SCRIPT%
echo.

REM Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    echo Please ensure the virtual environment is set up correctly.
    pause
    exit /b 1
)

REM Check if trigger script exists
if not exist "%TRIGGER_SCRIPT%" (
    echo ERROR: Trigger script not found at %TRIGGER_SCRIPT%
    pause
    exit /b 1
)

echo Creating scheduled task...
echo.

REM Create the scheduled task
schtasks /create /tn "WeeklyCEOBriefing" /tr "\"%PYTHON_EXE%\" \"%TRIGGER_SCRIPT%\"" /sc weekly /d MON /st 08:00 /f

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Scheduled task created!
    echo ========================================
    echo.
    echo Task Name: WeeklyCEOBriefing
    echo Schedule: Every Monday at 8:00 AM
    echo Action: Generate Weekly CEO Briefing
    echo.
    echo To view the task:
    echo   schtasks /query /tn "WeeklyCEOBriefing" /v /fo list
    echo.
    echo To run the task manually:
    echo   schtasks /run /tn "WeeklyCEOBriefing"
    echo.
    echo To delete the task:
    echo   schtasks /delete /tn "WeeklyCEOBriefing" /f
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Please run this script as Administrator.
    echo.
)

pause
