@echo off
REM Weekly Audit Execution Script for Windows
REM This script activates the virtual environment and runs the weekly audit

echo Starting Weekly CEO Briefing Audit...
echo.

REM Get the script directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Change to project root
cd /d "%PROJECT_ROOT%"

REM Activate virtual environment
if exist "app\.venv\Scripts\activate.bat" (
    call app\.venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found at app\.venv
    echo Please run: cd app ^&^& uv venv
    exit /b 1
)

REM Set vault path if not already set
if not defined AI_EMPLOYEE_VAULT (
    set AI_EMPLOYEE_VAULT=AI_Employee_Vault
)

REM Run the weekly audit
echo Running audit from vault: %AI_EMPLOYEE_VAULT%
python -m app.src.app.weekly_audit.audit_orchestrator

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Weekly audit completed successfully!
    exit /b 0
) else (
    echo.
    echo ERROR: Weekly audit failed with exit code %ERRORLEVEL%
    echo Check logs for details.
    exit /b %ERRORLEVEL%
)
