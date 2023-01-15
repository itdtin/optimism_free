@echo off
python -V
@echo Installing libraries...
python -m venv venv
venv\Scripts\activate && pip install -r requirements.txt
@echo To start the script run "start.bat"
pause
