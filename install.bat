@echo off
cd /d "%~dp0"
python -m pip install -q --no-warn-script-location .
if errorlevel 1 (echo Install failed. Make sure Python 3.10+ is installed and on PATH. & pause & exit /b 1)
for /f "delims=" %%S in ('python -c "import sysconfig;print(sysconfig.get_path('scripts'))"') do set "SCRIPTS=%%S"
powershell -NoProfile -Command "$p=[Environment]::GetEnvironmentVariable('Path','User'); if (($p -split ';') -notcontains '%SCRIPTS%') { [Environment]::SetEnvironmentVariable('Path', ($p.TrimEnd(';') + ';%SCRIPTS%'), 'User') }"
echo.
echo LARP installed. Open a NEW terminal and type:  larp
pause
