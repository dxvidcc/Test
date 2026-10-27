@echo off
cd /d "%~dp0"
set /p FARBE="Weiss oder Schwarz? (w/s): "
set COLOR=white
if /i "%FARBE%"=="s" set COLOR=black
python chesscoach.py --color %COLOR% --stockfish "%~dp0stockfish.exe"
pause