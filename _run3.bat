@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
set "QT_PLUGIN_PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\plugins"
set "PYTHONHOME=C:\GIT\FreeCAD\.pixi\envs\default"
set "PYTHONPATH=C:\GIT\FreeCAD\build\debug\Mod;C:\GIT\FreeCAD\build\debug\Ext;C:\GIT\FreeCAD\build\debug\lib;C:\GIT\FreeCAD\src\Ext;C:\GIT\FreeCAD\src"
set "PROJ_DATA=C:\GIT\FreeCAD\.pixi\envs\default\Library\share\proj"
set "PATH=C:\GIT\FreeCAD\build\debug\bin;C:\GIT\FreeCAD\.pixi\envs\default;C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;%PATH%"

C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "exec(open(r'C:\GIT\FreeCAD\_d.py').read())" 1> C:\GIT\FreeCAD\_stdout.txt 2> C:\GIT\FreeCAD\_stderr.txt
echo EXIT=%ERRORLEVEL% >> C:\GIT\FreeCAD\_stdout.txt
