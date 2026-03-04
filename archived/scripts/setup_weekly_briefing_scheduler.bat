@echo off
REM Weekly CEO Briefing Scheduler Setup
REM Right-click this file and select "Run as administrator"

echo ============================================================
echo Weekly CEO Briefing - Scheduler Setup
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires administrator privileges.
    echo         Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [INFO] Running with administrator privileges
echo.

REM Get the project root directory (parent of scripts folder)
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set APP_DIR=%PROJECT_ROOT%\app

echo [INFO] Project root: %PROJECT_ROOT%
echo [INFO] App directory: %APP_DIR%
echo.

REM Delete existing task if it exists
echo [INFO] Checking for existing task...
schtasks /delete /tn "WeeklyCEOBriefing" /f >nul 2>&1
if %errorLevel% equ 0 (
    echo [INFO] Deleted existing task 'WeeklyCEOBriefing'
) else (
    echo [INFO] No existing task found (this is OK)
)
echo.

REM Create the scheduled task using PowerShell
echo [INFO] Creating scheduled task...
echo.

powershell -Command "$action = New-ScheduledTaskAction -Execute '%SCRIPT_DIR%..\app\.venv\Scripts\python.exe' -Argument '-m src.app.weekly_audit.audit_orchestrator' -WorkingDirectory '%APP_DIR%'; $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '8:00PM'; $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$true -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances Queue; $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType ServiceAccount -RunLevel Highest; Register-ScheduledTask -TaskName 'WeeklyCEOBriefing' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force"

if %errorLevel% equ 0 (
    echo.
    echo [SUCCESS] Successfully created scheduled task 'WeeklyCEOBriefing'
    echo.
    echo Task Details:
    echo   - Name: WeeklyCEOBriefing
    echo   - Schedule: Every Sunday at 8:00 PM
    echo   - Command: python -m src.app.weekly_audit.audit_orchestrator
    echo   - Working Directory: %APP_DIR%
    echo.
    echo To verify the task was created, run:
    echo   schtasks /query /tn WeeklyCEOBriefing
    echo.
    echo To test the task manually, run:
    echo   schtasks /run /tn WeeklyCEOBriefing
    echo.
) else (
    echo.
    echo [ERROR] Failed to create scheduled task
    echo.
    echo Troubleshooting:
    echo   1. Make sure you're running as Administrator
    echo   2. Check that PowerShell execution policy allows scripts
    echo   3. Try running setup.py again as Administrator
    echo.
)

pause
