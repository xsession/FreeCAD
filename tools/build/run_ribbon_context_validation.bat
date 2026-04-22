@echo off
REM SPDX-License-Identifier: LGPL-2.1-or-later

setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "REPO_DIR=%%~fI"

if "%~1"=="" (
    set "FREECAD_RIBBON_CONTEXT_REPORT=%REPO_DIR%\build\testing_tmp_ribbon_context\report.txt"
) else (
    set "FREECAD_RIBBON_CONTEXT_REPORT=%~f1"
)

echo [RIBBON-VALIDATION] Report: %FREECAD_RIBBON_CONTEXT_REPORT%
call "%REPO_DIR%\run_freecad.bat" tests\test_ribbon_contextual_tabs.py

endlocal