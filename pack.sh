#!/bin/sh

python3 --version

pip3 install --upgrade pip

# create virtual env and install dependencies
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
pyinstaller --noconfirm --onefile --windowed --icon "./favicon.ico"  "./main.py" -n optimismQuests
