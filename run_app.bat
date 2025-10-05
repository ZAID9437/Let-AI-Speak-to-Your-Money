@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting AI Finance Assistant...
python app.py
pause
