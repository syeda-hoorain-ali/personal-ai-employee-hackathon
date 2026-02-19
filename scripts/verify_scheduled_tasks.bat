@echo off
echo ============================================================
echo Verifying Scheduled Tasks
echo ============================================================
echo.

echo [1] Checking LinkedIn Auto Poster...
schtasks /query /tn "LinkedInAutoPoster" /fo LIST 2>nul
if %errorLevel% equ 0 (
    echo [SUCCESS] LinkedInAutoPoster task found
) else (
    echo [WARNING] LinkedInAutoPoster task NOT found
)
echo.

echo [2] Checking Weekly CEO Briefing...
schtasks /query /tn "WeeklyCEOBriefing" /fo LIST 2>nul
if %errorLevel% equ 0 (
    echo [SUCCESS] WeeklyCEOBriefing task found
) else (
    echo [WARNING] WeeklyCEOBriefing task NOT found
)
echo.

echo ============================================================
echo Summary
echo ============================================================
echo.
echo If both tasks show [SUCCESS], your setup is complete!
echo.
echo To test the Weekly CEO Briefing manually:
echo   schtasks /run /tn WeeklyCEOBriefing
echo.
pause
