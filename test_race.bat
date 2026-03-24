@echo off
echo Starting the Flask app...
start /B python app/app.py
timeout /t 3 /nobreak > nul
echo Opening browser to test race page...
start http://localhost:5000/test_race
echo Done.