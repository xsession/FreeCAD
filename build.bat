@echo off
REM SPDX-License-Identifier: LGPL-2.1-or-later
REM
REM FreeCAD Windows Build Automation Script
REM Usage: build.bat [command]
REM
REM Commands:
REM   (none)     Full build (install pixi, configure, build, install)
REM   configure  CMake configure only
REM   build      Compile only (incremental)
REM   test       Run all tests
REM   run        Launch FreeCAD
REM   clean      Remove build directory
REM   release    Full optimized release build
REM   debug      Full debug build
REM   all        Configure + Build + Test + Install
REM
REM Works from a completely clean Windows 10/11 machine.

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "BUILD_DIR=%SCRIPT_DIR%build"

REM Detect number of CPU cores for parallel compilation
set "NPROC=%NUMBER_OF_PROCESSORS%"
if not defined NPROC set "NPROC=4"

REM Parse command early so we can avoid unnecessary compiler bootstrap
set "CMD=%~1"

REM ---- Check/Install pixi ----
:check_pixi
set "PATH=%USERPROFILE%\.pixi\bin;%PATH%"
where pixi >nul 2>&1
if %errorlevel% neq 0 (
    echo [BUILD] pixi not found. Installing pixi...
    powershell -ExecutionPolicy Bypass -Command "iwr -useb https://pixi.sh/install.ps1 | iex"
    echo [BUILD] Install script finished. Verifying...
)
where pixi >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pixi. Binary not found on PATH.
    echo         Please install pixi manually from https://pixi.sh
    exit /b 1
)

REM ---- Check/Init git submodules ----
:check_submodules
if not exist "%SCRIPT_DIR%tests\lib\googletest\CMakeLists.txt" (
    echo [BUILD] Initializing git submodules...
    cd "%SCRIPT_DIR%"
    git submodule update --init --recursive
)
if not exist "%SCRIPT_DIR%tests\lib\googletest\CMakeLists.txt" (
    echo [ERROR] Failed to initialize git submodules.
    echo         Please run: git submodule update --init --recursive
    exit /b 1
)

REM ---- Set up Visual Studio compiler environment if cl.exe not found ----
:check_compiler
if /I "%CMD%"=="run" goto :compiler_ok
if /I "%CMD%"=="test" goto :compiler_ok
if /I "%CMD%"=="clean" goto :compiler_ok

REM Use delayed expansion for ProgramFiles(x86) ? parens break normal expansion
set "VSWHERE=!ProgramFiles(x86)!\Microsoft Visual Studio\Installer\vswhere.exe"
where cl.exe >nul 2>&1
if !errorlevel! equ 0 goto :compiler_ok

echo [BUILD] cl.exe not found. Setting up Visual Studio environment...

if not exist "!VSWHERE!" (
    echo [ERROR] Visual Studio not found. Please install Visual Studio 2019 or later
    echo         with the "Desktop development with C++" workload.
    exit /b 1
)

REM Find the latest VS installation
for /f "usebackq tokens=*" %%i in (`"!VSWHERE!" -latest -property installationPath`) do set "VSDIR=%%i"
if not defined VSDIR (
    echo [ERROR] No Visual Studio installation found via vswhere.
    exit /b 1
)

REM Initialize the VS developer environment (x64)
if exist "!VSDIR!\VC\Auxiliary\Build\vcvars64.bat" (
    echo [BUILD] Found Visual Studio at: !VSDIR!
    set "VCVARS_BAT=!VSDIR!\VC\Auxiliary\Build\vcvars64.bat"
    for /f "delims=" %%E in ('cmd /d /q /c ""!VCVARS_BAT!" >nul 2>&1 && set"') do set "%%E"
) else (
    echo [ERROR] vcvars64.bat not found. Install "Desktop development with C++".
    exit /b 1
)

where cl.exe >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] cl.exe still not found after VS environment setup.
    exit /b 1
)

:compiler_ok
for /f "tokens=*" %%v in ('cl.exe 2^>^&1 ^| findstr /C:"Version"') do echo [BUILD] Compiler: %%v

REM ---- Prepare pixi prefix paths without replacing MSVC LIB/INCLUDE ----
set "PIXI_ENV=%SCRIPT_DIR%.pixi\envs\default"
set "CONDA_PREFIX=%PIXI_ENV%"
set "PATH=%PIXI_ENV%;%PIXI_ENV%\Library\bin;%PIXI_ENV%\Scripts;%PATH%"
set "LIB=%PIXI_ENV%\Library\lib;%LIB%"
set "INCLUDE=%PIXI_ENV%\Library\include;%INCLUDE%"

REM ---- Parse command ----
if "%CMD%"=="" goto :full_build
if "%CMD%"=="configure" goto :configure
if "%CMD%"=="build" goto :build
if "%CMD%"=="test" goto :test
if "%CMD%"=="run" goto :run
if "%CMD%"=="clean" goto :clean
if "%CMD%"=="release" goto :release
if "%CMD%"=="debug" goto :debug_build
if "%CMD%"=="all" goto :all
echo [ERROR] Unknown command: %CMD%
echo Usage: build.bat [configure^|build^|test^|run^|clean^|release^|debug^|all]
exit /b 1

REM ---- Commands ----

:configure
echo [BUILD] Configuring with CMake...
cd "%SCRIPT_DIR%"
set "CFLAGS="
set "CXXFLAGS="
set "DEBUG_CFLAGS="
set "DEBUG_CXXFLAGS="
set "LDFLAGS="
set "LIBS="
cmake --preset conda-windows-debug -DCMAKE_GENERATOR_PLATFORM= -DCMAKE_GENERATOR_TOOLSET=
if %errorlevel% neq 0 (
    echo [ERROR] CMake configuration failed.
    echo         Check that all dependencies are available via pixi.
    exit /b 1
)
echo [BUILD] Configuration complete.
goto :eof

:build
echo [BUILD] Building with %NPROC% parallel jobs...
cd "%SCRIPT_DIR%"
set "BUILD_LOG=%TEMP%\freecad_build_%RANDOM%.log"
set "ICE_RETRIES=0"
set "MAX_ICE_RETRIES=3"
set "CCACHE_EXE=%SCRIPT_DIR%.pixi\envs\default\Library\bin\ccache.exe"

:build_attempt
powershell -NoProfile -Command "cmake --build '%SCRIPT_DIR%build\debug' --parallel %NPROC% 2>&1 | Tee-Object -FilePath '!BUILD_LOG!'; exit $LASTEXITCODE"
set "BUILD_ERR=!errorlevel!"
if !BUILD_ERR! equ 0 goto :build_done

REM Check for MSVC Internal Compiler Error (C1001), commonly caused by ccache + /Z7 + /MP
findstr /C:"fatal error C1001" "!BUILD_LOG!" >nul 2>&1
if !errorlevel! neq 0 (
    if exist "!BUILD_LOG!" del "!BUILD_LOG!"
    echo [ERROR] Build failed.
    echo         Check the compiler output above for specific errors.
    exit /b 1
)

REM ICE detected - clear ccache and retry
set /a ICE_RETRIES+=1
if !ICE_RETRIES! gtr %MAX_ICE_RETRIES% (
    if exist "!BUILD_LOG!" del "!BUILD_LOG!"
    echo [ERROR] Build failed with MSVC Internal Compiler Error ^(C1001^) after %MAX_ICE_RETRIES% retries.
    echo         Consider upgrading to Visual Studio 2022 or disabling ccache.
    exit /b 1
)

echo.
echo [BUILD] *** MSVC Internal Compiler Error ^(C1001^) detected ***
echo [BUILD] This is a known MSVC bug triggered by ccache + /Z7 + /MP.
echo [BUILD] Clearing ccache and retrying ^(attempt !ICE_RETRIES!/%MAX_ICE_RETRIES%^)...
if exist "!CCACHE_EXE!" (
    "!CCACHE_EXE!" -C
    echo [BUILD] ccache cleared.
) else (
    echo [BUILD] ccache not found at !CCACHE_EXE!, skipping cache clear.
)
echo.
goto :build_attempt

:build_done
if exist "!BUILD_LOG!" del "!BUILD_LOG!"
echo [BUILD] Build complete.
goto :eof

:test
echo [BUILD] Running tests...
cd "%SCRIPT_DIR%"
set "TEST_PATH=%SCRIPT_DIR%build\debug\bin;%SCRIPT_DIR%build\debug\lib;%SCRIPT_DIR%build\debug\Mod"
for /d %%D in ("%SCRIPT_DIR%build\debug\Mod\*") do (
    set "TEST_PATH=!TEST_PATH!;%%~fD"
)
set "PATH=!TEST_PATH!;%PIXI_ENV%\Library\bin;%PIXI_ENV%\Library\lib;%PIXI_ENV%;%PIXI_ENV%\Scripts;%PIXI_ENV%\bin;%PATH%"

ctest --test-dir "%SCRIPT_DIR%build\debug"
if %errorlevel% neq 0 (
    echo [WARNING] Some tests failed. Check output above.
    exit /b 1
)
echo [BUILD] All tests passed.
goto :eof

:run
echo [BUILD] Launching FreeCAD...
cd "%SCRIPT_DIR%"
call "%SCRIPT_DIR%run_freecad.bat" %2 %3 %4 %5
goto :eof

:clean
echo [BUILD] Cleaning build directory...
if exist "%BUILD_DIR%" (
    rmdir /s /q "%BUILD_DIR%"
    echo [BUILD] Build directory removed.
) else (
    echo [BUILD] Build directory does not exist. Nothing to clean.
)
goto :eof

:release
echo [BUILD] Full release build...
cd "%SCRIPT_DIR%"
set "CFLAGS="
set "CXXFLAGS="
set "DEBUG_CFLAGS="
set "DEBUG_CXXFLAGS="
set "LDFLAGS="
set "LIBS="
cmake --preset conda-windows-release -DCMAKE_GENERATOR_PLATFORM= -DCMAKE_GENERATOR_TOOLSET=
if %errorlevel% neq 0 (
    echo [ERROR] Configure failed.
    exit /b 1
)
call :build
if %errorlevel% neq 0 exit /b 1
echo [BUILD] Release build complete.
goto :eof

:debug_build
echo [BUILD] Full debug build...
cd "%SCRIPT_DIR%"
cmake -B "%BUILD_DIR%" -S "%SCRIPT_DIR%" -DCMAKE_BUILD_TYPE=Debug
if %errorlevel% neq 0 (
    echo [ERROR] Debug configure failed.
    exit /b 1
)
set "DBG_LOG=%TEMP%\freecad_debug_build_%RANDOM%.log"
set "DBG_ICE_RETRIES=0"
set "CCACHE_EXE=%SCRIPT_DIR%.pixi\envs\default\Library\bin\ccache.exe"

:debug_build_attempt
powershell -NoProfile -Command "cmake --build '%BUILD_DIR%' --parallel %NPROC% 2>&1 | Tee-Object -FilePath '!DBG_LOG!'; exit $LASTEXITCODE"
set "DBG_ERR=!errorlevel!"
if !DBG_ERR! equ 0 (
    if exist "!DBG_LOG!" del "!DBG_LOG!"
    echo [BUILD] Debug build complete.
    goto :eof
)

findstr /C:"fatal error C1001" "!DBG_LOG!" >nul 2>&1
if !errorlevel! neq 0 (
    if exist "!DBG_LOG!" del "!DBG_LOG!"
    echo [ERROR] Debug build failed.
    exit /b 1
)

set /a DBG_ICE_RETRIES+=1
if !DBG_ICE_RETRIES! gtr 3 (
    if exist "!DBG_LOG!" del "!DBG_LOG!"
    echo [ERROR] Debug build failed with MSVC ICE ^(C1001^) after 3 retries.
    exit /b 1
)

echo.
echo [BUILD] *** MSVC Internal Compiler Error ^(C1001^) detected ***
echo [BUILD] Clearing ccache and retrying ^(attempt !DBG_ICE_RETRIES!/3^)...
if exist "!CCACHE_EXE!" (
    "!CCACHE_EXE!" -C
    echo [BUILD] ccache cleared.
)
echo.
goto :debug_build_attempt

:all
echo [BUILD] Full pipeline: Configure + Build + Test + Install
call :configure
if %errorlevel% neq 0 exit /b 1
call :build
if %errorlevel% neq 0 exit /b 1
call :test
echo [BUILD] All steps complete.
goto :eof

:full_build
echo ================================================================
echo   FreeCAD Build Script
echo   Cores: %NPROC%
echo ================================================================
call :configure
if %errorlevel% neq 0 exit /b 1
call :build
if %errorlevel% neq 0 exit /b 1
echo [BUILD] Full build complete. Run 'build.bat run' to launch FreeCAD.
goto :eof
