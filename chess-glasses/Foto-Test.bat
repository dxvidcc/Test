@echo off
rem Fotos von einem Schachbrett auf diese Datei ziehen.
cd /d "%~dp0"
set PYTHONUTF8=1
set /p FARBE="Wer ist am Zug? (w/s): "
set COLOR=white
if /i "%FARBE%"=="s" set COLOR=black
python chesscoach.py --photo %* --color %COLOR% --stockfish "%~dp0stockfish.exe"
pause
