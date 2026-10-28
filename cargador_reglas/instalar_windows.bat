@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
    echo Instale Python 3.9 o superior desde python.org, incluido el lanzador py.
    pause
    exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto error
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Instalacion terminada. Abra iniciar_windows.bat.
pause
exit /b 0
:error
echo La instalacion no termino. Revise el mensaje anterior y la conexion a Internet.
pause
exit /b 1
