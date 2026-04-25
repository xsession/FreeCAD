@echo off
REM SPDX-License-Identifier: LGPL-2.1-or-later
REM
REM FreeCAD Launcher ? sets all required environment variables and starts FreeCAD.
REM
REM Usage:
REM   run_freecad.bat              Launch FreeCAD GUI
REM   run_freecad.bat --console    Launch FreeCAD console (no GUI)
REM   run_freecad.bat script.py    Execute a Python GUI script via a temporary FCMacro wrapper
REM   run_freecad.bat [any args]   Launch FreeCAD GUI with extra arguments
REM
REM This script auto-detects the pixi environment, build output directory,
REM and all runtime paths (Qt plugins, Python, PROJ, OpenSSL, OpenCL, etc.)

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "DEFAULT_LOG_DIR=%TEMP%\FreeCAD\launcher-logs"
set "LOG_DIR=%DEFAULT_LOG_DIR%"
set "AUTO_LOG=1"
set "DIAGNOSTIC_STARTUP=0"
set "USER_SUPPLIED_LOG=0"
set "FC_LOG_FILE="
set "LAUNCH_SCRIPT="
set "LAUNCH_WRAPPER="

REM ---- Detect build directory (debug first, then release) ----
set "BUILD_BIN="
if exist "%SCRIPT_DIR%build\debug\bin\FreeCAD.exe" (
    set "BUILD_BIN=%SCRIPT_DIR%build\debug\bin"
    set "BUILD_LIB=%SCRIPT_DIR%build\debug\lib"
    set "BUILD_MOD=%SCRIPT_DIR%build\debug\Mod"
    set "BUILD_DATA=%SCRIPT_DIR%build\debug\data"
    echo [LAUNCHER] Using debug build
) else if exist "%SCRIPT_DIR%build\release\bin\FreeCAD.exe" (
    set "BUILD_BIN=%SCRIPT_DIR%build\release\bin"
    set "BUILD_LIB=%SCRIPT_DIR%build\release\lib"
    set "BUILD_MOD=%SCRIPT_DIR%build\release\Mod"
    set "BUILD_DATA=%SCRIPT_DIR%build\release\data"
    echo [LAUNCHER] Using release build
) else (
    echo [ERROR] No FreeCAD build found.
    echo         Expected: build\debug\bin\FreeCAD.exe or build\release\bin\FreeCAD.exe
    echo         Run 'build.bat' first.
    exit /b 1
)

REM ---- Detect pixi environment ----
set "PIXI_ENV=%SCRIPT_DIR%.pixi\envs\default"
if not exist "!PIXI_ENV!\Library\bin" (
    echo [ERROR] Pixi environment not found at: !PIXI_ENV!
    echo         Run 'pixi install' first.
    exit /b 1
)
echo [LAUNCHER] Pixi env: !PIXI_ENV!

REM ---- PATH: build output + pixi libraries + pixi base ----
set "PATH=!BUILD_BIN!;!BUILD_LIB!;!PIXI_ENV!\Library\bin;!PIXI_ENV!\Library\lib;!PIXI_ENV!;!PIXI_ENV!\Scripts;!PIXI_ENV!\bin;%PATH%"

REM ---- Qt 6 plugin path (required ? FreeCAD won't start without this) ----
set "QT_PLUGIN_PATH=!PIXI_ENV!\Library\lib\qt6\plugins"
if not exist "!QT_PLUGIN_PATH!\platforms" (
    echo [ERROR] Qt platform plugins not found at: !QT_PLUGIN_PATH!
    exit /b 1
)

REM ---- Python (embedded in pixi env) ----
set "PYTHONHOME=!PIXI_ENV!"
set "PYTHONPATH=!BUILD_LIB!;!BUILD_MOD!;%SCRIPT_DIR%src\Mod;%SCRIPT_DIR%src\Ext;%SCRIPT_DIR%src\Gui"

REM ---- PROJ (geospatial coordinate transforms ? used by some workbenches) ----
if exist "!PIXI_ENV!\Library\share\proj" (
    set "PROJ_DATA=!PIXI_ENV!\Library\share\proj"
)

REM ---- OpenSSL (certificate paths for network operations) ----
if exist "!PIXI_ENV!\Library\ssl\cacert.pem" (
    if not defined SSL_CERT_FILE set "SSL_CERT_FILE=!PIXI_ENV!\Library\ssl\cacert.pem"
)
if exist "!PIXI_ENV!\Library\ssl\certs" (
    if not defined SSL_CERT_DIR set "SSL_CERT_DIR=!PIXI_ENV!\Library\ssl\certs"
)

REM ---- OpenCL ICD (GPU compute ? used by some FEM solvers) ----
if exist "!PIXI_ENV!\Library\etc\OpenCL\vendors" (
    REM Let the pixi OpenCL helper populate this if needed
    set "OCL_ICD_FILENAMES="
)

REM ---- FreeCAD-specific env ----
REM Tell FreeCAD where its resources are (only needed for non-installed builds)
if exist "!BUILD_DATA!" (
    set "FREECAD_DATA_DIR=!BUILD_DATA!"
)

REM ---- Determine which executable to run ----
set "FC_EXE=FreeCAD.exe"
set "FC_ARGS=-P "%SCRIPT_DIR%src\Gui""

:parse_args
if "%~1"=="" goto :launch
if /i "%~1"=="--console" (
    set "FC_EXE=FreeCADCmd.exe"
    shift
    goto :parse_args
)
if /i "%~1"=="--run-script" (
    if "%~2"=="" (
        echo [ERROR] --run-script requires a Python file path.
        exit /b 1
    )
    set "LAUNCH_SCRIPT=%~f2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--diagnostic-startup" (
    set "DIAGNOSTIC_STARTUP=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--no-log" (
    set "AUTO_LOG=0"
    shift
    goto :parse_args
)
if /i "%~1"=="--log-dir" (
    if "%~2"=="" (
        echo [ERROR] --log-dir requires a directory path.
        exit /b 1
    )
    set "LOG_DIR=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--log-file" set "USER_SUPPLIED_LOG=1"
if /i "%~1"=="--write-log" set "USER_SUPPLIED_LOG=1"
if /i "%~1"=="-l" set "USER_SUPPLIED_LOG=1"
if not defined LAUNCH_SCRIPT if /i "%~x1"==".py" if exist "%~1" (
    set "LAUNCH_SCRIPT=%~f1"
    shift
    goto :parse_args
)
REM Collect remaining args
set "FC_ARGS=!FC_ARGS! %1"
shift
goto :parse_args

:launch
if defined LAUNCH_SCRIPT call :prepare_python_launcher
if "%AUTO_LOG%"=="1" if "%USER_SUPPLIED_LOG%"=="0" call :configure_log_file
if "%DIAGNOSTIC_STARTUP%"=="1" call :enable_diagnostic_startup

echo [LAUNCHER] Starting !FC_EXE!...
echo [LAUNCHER] QT_PLUGIN_PATH = !QT_PLUGIN_PATH!
echo [LAUNCHER] PYTHONHOME     = !PYTHONHOME!
echo [LAUNCHER] PROJ_DATA      = !PROJ_DATA!
if defined LAUNCH_SCRIPT echo [LAUNCHER] SCRIPT         = !LAUNCH_SCRIPT!
if defined FC_LOG_FILE echo [LAUNCHER] LOG_FILE       = !FC_LOG_FILE!
if "%DIAGNOSTIC_STARTUP%"=="1" echo [LAUNCHER] Diagnostic startup logging enabled
echo.

"!BUILD_BIN!\!FC_EXE!" !FC_ARGS!
set "FC_EXIT=!errorlevel!"

if defined FC_LOG_FILE call :print_log_summary

if !FC_EXIT! neq 0 (
    echo.
    echo [LAUNCHER] FreeCAD exited with code !FC_EXIT!
    if !FC_EXIT! equ -1073741515 (
        echo [LAUNCHER] This is STATUS_DLL_NOT_FOUND ? a required DLL is missing from PATH.
        echo            Try running: where /R "!BUILD_BIN!" *.dll
    )
    if !FC_EXIT! equ -1073741701 (
        echo [LAUNCHER] This is STATUS_DLL_INIT_FAILED ? a DLL failed to initialize.
        echo            Check that all pixi dependencies are installed: pixi install
    )
    call :print_crash_artifacts
)

exit /b !FC_EXIT!

:configure_log_file
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd-HHmmss'"') do set "FC_LOG_STAMP=%%I"
set "FC_LOG_FILE=%LOG_DIR%\%FC_EXE:~0,-4%-%FC_LOG_STAMP%.log"
set "FC_ARGS=!FC_ARGS! --log-file "!FC_LOG_FILE!""
goto :eof

:enable_diagnostic_startup
set "QT_DEBUG_PLUGINS=1"
set "QT_LOGGING_RULES=qt.qpa.*=true;qt.core.plugin.*=true"
set "FC_LAUNCH_DIAGNOSTIC_STARTUP=1"
goto :eof

:prepare_python_launcher
if not exist "%TEMP%\FreeCAD\launcher-scripts" mkdir "%TEMP%\FreeCAD\launcher-scripts" >nul 2>&1
set "LAUNCH_WRAPPER=%TEMP%\FreeCAD\launcher-scripts\run_python_script.FCMacro"
powershell -NoProfile -Command "$content = @('import os','import runpy','import sys','','script = os.environ.get(''FREECAD_LAUNCH_SCRIPT'', '''')','if not script:','    raise RuntimeError(''FREECAD_LAUNCH_SCRIPT not set'')','','sys.argv = [script]','runpy.run_path(script, run_name=''__main__'')'); Set-Content -LiteralPath '!LAUNCH_WRAPPER!' -Value $content -Encoding ASCII"
if errorlevel 1 (
    echo [ERROR] Failed to prepare Python launcher wrapper.
    exit /b 1
)
set "FREECAD_LAUNCH_SCRIPT=!LAUNCH_SCRIPT!"
set "FC_ARGS=!FC_ARGS! ^"!LAUNCH_WRAPPER!^""
goto :eof

:print_log_summary
if not exist "!FC_LOG_FILE!" goto :eof
echo [LAUNCHER] Recent log summary:
powershell -NoProfile -Command "$p='!FC_LOG_FILE!'; $patterns='^(Err:|Wrn:|Log: .*failed|Log: Traceback|Log: .*ModuleNotFoundError|Log: .*ImportError)'; $lines=Get-Content $p | Where-Object { $_ -match $patterns } | Select-Object -Last 12; if ($lines) { $lines | ForEach-Object { $_ } } else { '[LAUNCHER]   no warning/error lines captured' }"
goto :eof

:print_crash_artifacts
for %%D in ("%APPDATA%\FreeCAD" "%APPDATA%\FreeCAD\v1-2") do (
    if exist %%~fD (
        powershell -NoProfile -Command "$dir='%%~fD'; $items=Get-ChildItem $dir -Filter 'crash.*' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 4; if ($items) { '[LAUNCHER] Crash artifacts:'; $items | ForEach-Object { '[LAUNCHER]   ' + $_.FullName } }"
    )
)
goto :eof
