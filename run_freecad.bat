@echo off
REM SPDX-License-Identifier: LGPL-2.1-or-later
REM
REM FreeCAD Launcher — sets all required environment variables and starts FreeCAD.
REM
REM Usage:
REM   run_freecad.bat              Launch FreeCAD GUI
REM   run_freecad.bat --console    Launch FreeCAD console (no GUI)
REM   run_freecad.bat [any args]   Launch FreeCAD GUI with extra arguments
REM
REM This script auto-detects the pixi environment, build output directory,
REM and all runtime paths (Qt plugins, Python, PROJ, OpenSSL, OpenCL, etc.)

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"

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

REM ---- Qt 6 plugin path (required — FreeCAD won't start without this) ----
set "QT_PLUGIN_PATH=!PIXI_ENV!\Library\lib\qt6\plugins"
if not exist "!QT_PLUGIN_PATH!\platforms" (
    echo [ERROR] Qt platform plugins not found at: !QT_PLUGIN_PATH!
    exit /b 1
)

REM ---- Python (embedded in pixi env) ----
set "PYTHONHOME=!PIXI_ENV!"
set "PYTHONPATH=!BUILD_LIB!;!BUILD_MOD!;%SCRIPT_DIR%src\Mod;%SCRIPT_DIR%src\Ext"

REM ---- PROJ (geospatial coordinate transforms — used by some workbenches) ----
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

REM ---- OpenCL ICD (GPU compute — used by some FEM solvers) ----
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
set "FC_ARGS="

:parse_args
if "%~1"=="" goto :launch
if /i "%~1"=="--console" (
    set "FC_EXE=FreeCADCmd.exe"
    shift
    goto :parse_args
)
REM Collect remaining args
set "FC_ARGS=!FC_ARGS! %1"
shift
goto :parse_args

:launch
echo [LAUNCHER] Starting !FC_EXE!...
echo [LAUNCHER] QT_PLUGIN_PATH = !QT_PLUGIN_PATH!
echo [LAUNCHER] PYTHONHOME     = !PYTHONHOME!
echo [LAUNCHER] PROJ_DATA      = !PROJ_DATA!
echo.

"!BUILD_BIN!\!FC_EXE!" !FC_ARGS!
set "FC_EXIT=!errorlevel!"

if !FC_EXIT! neq 0 (
    echo.
    echo [LAUNCHER] FreeCAD exited with code !FC_EXIT!
    if !FC_EXIT! equ -1073741515 (
        echo [LAUNCHER] This is STATUS_DLL_NOT_FOUND — a required DLL is missing from PATH.
        echo            Try running: where /R "!BUILD_BIN!" *.dll
    )
    if !FC_EXIT! equ -1073741701 (
        echo [LAUNCHER] This is STATUS_DLL_INIT_FAILED — a DLL failed to initialize.
        echo            Check that all pixi dependencies are installed: pixi install
    )
)

exit /b !FC_EXIT!
