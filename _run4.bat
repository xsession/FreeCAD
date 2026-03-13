@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
set "QT_PLUGIN_PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\plugins"
set "PYTHONHOME=C:\GIT\FreeCAD\.pixi\envs\default"
set "PYTHONPATH=C:\GIT\FreeCAD\build\debug\Mod;C:\GIT\FreeCAD\build\debug\Ext;C:\GIT\FreeCAD\build\debug\lib;C:\GIT\FreeCAD\src\Ext;C:\GIT\FreeCAD\src"
set "PROJ_DATA=C:\GIT\FreeCAD\.pixi\envs\default\Library\share\proj"
set "PATH=C:\GIT\FreeCAD\build\debug\bin;C:\GIT\FreeCAD\.pixi\envs\default;C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;%PATH%"

echo TEST1: basic print > C:\GIT\FreeCAD\_t.txt
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "import sys; sys.stdout.write('HELLO\n'); sys.stdout.flush(); sys.exit(0)" 1>> C:\GIT\FreeCAD\_t.txt 2>> C:\GIT\FreeCAD\_t.txt
echo EC1=%ERRORLEVEL% >> C:\GIT\FreeCAD\_t.txt

echo TEST2: import FreeCAD >> C:\GIT\FreeCAD\_t.txt
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "import FreeCAD; import sys; sys.stdout.write('FC_OK\n'); sys.stdout.flush(); sys.exit(0)" 1>> C:\GIT\FreeCAD\_t.txt 2>> C:\GIT\FreeCAD\_t.txt
echo EC2=%ERRORLEVEL% >> C:\GIT\FreeCAD\_t.txt

echo TEST3: import Part >> C:\GIT\FreeCAD\_t.txt
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "import FreeCAD, Part; import sys; sys.stdout.write('PART_OK\n'); sys.stdout.flush(); sys.exit(0)" 1>> C:\GIT\FreeCAD\_t.txt 2>> C:\GIT\FreeCAD\_t.txt
echo EC3=%ERRORLEVEL% >> C:\GIT\FreeCAD\_t.txt

echo TEST4: makeBox >> C:\GIT\FreeCAD\_t.txt
C:\GIT\FreeCAD\build\debug\bin\FreeCADCmd.exe -c "import FreeCAD, Part; b=Part.makeBox(10,10,10); import sys; sys.stdout.write('BOX faces=%d\n' %% len(b.Faces)); sys.stdout.flush(); sys.exit(0)" 1>> C:\GIT\FreeCAD\_t.txt 2>> C:\GIT\FreeCAD\_t.txt
echo EC4=%ERRORLEVEL% >> C:\GIT\FreeCAD\_t.txt
