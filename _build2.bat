@echo off
echo STARTING_BUILD > C:\GIT\FreeCAD\_blog2.txt

call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
echo VCVARS_DONE >> C:\GIT\FreeCAD\_blog2.txt

set "PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;C:\GIT\FreeCAD\.pixi\envs\default;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\bin;%PATH%"
echo PATH_SET >> C:\GIT\FreeCAD\_blog2.txt

cd /d C:\GIT\FreeCAD\build\debug
echo CD_DONE >> C:\GIT\FreeCAD\_blog2.txt

ninja -j4 src/Mod/Part/App/CMakeFiles/Part.dir/TopoShape.cpp.obj src/Mod/Part/App/CMakeFiles/Part.dir/TopoShapeExpansion.cpp.obj >> C:\GIT\FreeCAD\_blog2.txt 2>&1
echo COMPILE_EXIT=%ERRORLEVEL% >> C:\GIT\FreeCAD\_blog2.txt

ninja -j4 Part >> C:\GIT\FreeCAD\_blog2.txt 2>&1
echo LINK_EXIT=%ERRORLEVEL% >> C:\GIT\FreeCAD\_blog2.txt

echo BUILD_COMPLETE >> C:\GIT\FreeCAD\_blog2.txt
