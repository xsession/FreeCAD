# PowerShell build script
$ErrorActionPreference = "Continue"

# Set up environment
$env:PATH = "C:\GIT\FreeCAD\.pixi\envs\default\Library\bin;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib;C:\GIT\FreeCAD\.pixi\envs\default;C:\GIT\FreeCAD\.pixi\envs\default\Library\lib\qt6\bin;$env:PATH"

# Initialize MSVC
$vsWhere = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName = "cmd.exe"
$pinfo.Arguments = "/c `"call `"$vsWhere`" > nul 2>&1 && cd /d C:\GIT\FreeCAD\build\debug && ninja -j4 src/Mod/Part/App/CMakeFiles/Part.dir/TopoShape.cpp.obj src/Mod/Part/App/CMakeFiles/Part.dir/TopoShapeExpansion.cpp.obj && echo COMPILE_OK || echo COMPILE_FAIL && ninja -j4 Part && echo LINK_OK || echo LINK_FAIL`""
$pinfo.RedirectStandardOutput = $true
$pinfo.RedirectStandardError = $true
$pinfo.UseShellExecute = $false
$pinfo.CreateNoWindow = $true

# Propagate PATH
$pinfo.EnvironmentVariables["PATH"] = $env:PATH

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $pinfo
$proc.Start() | Out-Null

$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()

$stdout | Out-File "C:\GIT\FreeCAD\_blog.txt" -Encoding UTF8
$stderr | Out-File "C:\GIT\FreeCAD\_berr.txt" -Encoding UTF8

Write-Host "Exit code: $($proc.ExitCode)"
Write-Host "=== LAST 20 STDOUT ==="
$stdout -split "`n" | Select-Object -Last 20
