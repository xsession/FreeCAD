@echo off
setlocal
set "ROOT=%~dp0"
set "PS=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%build.ps1" %*
exit /b %ERRORLEVEL%

