@echo off
rem Waehrend der Anruf laeuft starten: du solltest "Test. Springer f3." in der Brille hoeren.
cd /d "%~dp0"
python chesscoach.py --test-voice
pause
