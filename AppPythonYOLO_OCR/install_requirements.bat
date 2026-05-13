@echo off
cd /d "%~dp0"
echo Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Done.
pause
