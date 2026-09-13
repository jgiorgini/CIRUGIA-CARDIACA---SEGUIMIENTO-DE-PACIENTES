@echo off
cd /d "%~dp0"
if exist data\rcv.db del /q data\rcv.db
if exist data\rcv.db-wal del /q data\rcv.db-wal
if exist data\rcv.db-shm del /q data\rcv.db-shm
echo Datos locales eliminados. La proxima apertura comenzara sin pacientes/casos.
pause
