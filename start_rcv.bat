@echo off
title RCV-V1.0-LOCAL-004 - PUERTO 8767
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python no esta instalado o no esta en PATH.
  echo Instale Python 3 desde python.org y vuelva a ejecutar este archivo.
  pause
  exit /b 1
)
python server.py
pause
