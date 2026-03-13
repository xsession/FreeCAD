@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
set "QT_PLUGIN_PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\plugins"
set "PYTHONHOME=C:\GIT\FreeCAD\.pixi\envs\default"
set "PYTHONPATH=C:\GIT\FreeCAD\build\debug\Mod;C:\GIT\FreeCAD\build\debug\Ext;C:\GIT\FreeCAD\build\debug\lib;C:\GIT\FreeCAD\src\Ext;C:\GIT\FreeCAD\src"
set "PROJ_DATA=C:\GIT\FreeCAD\.pixi\envs\default\Library\share\proj"
set "PATH=C:\GIT\FreeCAD\build\debug\bin;C:\GIT\FreeCAD\.pixi\envs\default;C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;%PATH%"

echo STEP1: checking exe exists > C:\GIT\FreeCAD\_d_out2.txt
if exist "C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe" (
    echo EXE EXISTS >> C:\GIT\FreeCAD\_d_out2.txt
) else (
    echo EXE NOT FOUND >> C:\GIT\FreeCAD\_d_out2.txt
    goto :eof
)

echo STEP2: running simple test >> C:\GIT\FreeCAD\_d_out2.txt
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "print('HELLO'); import sys; sys.exit(0)" >> C:\GIT\FreeCAD\_d_out2.txt 2>&1
echo EXITCODE1=%ERRORLEVEL% >> C:\GIT\FreeCAD\_d_out2.txt
