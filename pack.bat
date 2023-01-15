@echo off
python -V
@echo Installing libraries...
python -m venv venv
venv\Scripts\activate && pip install -r requirements.txt && pyinstaller --noconfirm --onefile --windowed --icon "./favicon.ico"  "./main.py" -n optimismQuests
pause
