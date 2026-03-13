@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" > nul 2>&1
cd /d C:\GIT\FreeCAD\build\debug
echo === Building ImpExpDxf.cpp.obj ===
ninja -j1 src/Mod/Import/App/CMakeFiles/Import.dir/dxf/ImpExpDxf.cpp.obj
echo === EXIT CODE: %ERRORLEVEL% ===
echo === Building ImpExpDxfCallbacks.cpp.obj ===
ninja -j1 src/Mod/Import/App/CMakeFiles/Import.dir/dxf/ImpExpDxfCallbacks.cpp.obj
echo === EXIT CODE: %ERRORLEVEL% ===
echo === Building ImpExpDxfWrite.cpp.obj ===
ninja -j1 src/Mod/Import/App/CMakeFiles/Import.dir/dxf/ImpExpDxfWrite.cpp.obj
echo === EXIT CODE: %ERRORLEVEL% ===
