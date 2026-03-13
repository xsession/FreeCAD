@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
set "PATH=C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;C:\GIT\FreeCAD\.pixi\envs\default;%PATH%"
cd /d C:\GIT\FreeCAD\build\debug

echo BUILDING_STARTED
ninja -j4 src/Mod/Part/App/CMakeFiles/Part.dir/TopoShape.cpp.obj src/Mod/Part/App/CMakeFiles/Part.dir/TopoShapeExpansion.cpp.obj 2>&1
echo COMPILE_DONE_%ERRORLEVEL%

echo LINKING_PART
ninja -j4 Part 2>&1
echo LINK_DONE_%ERRORLEVEL%
