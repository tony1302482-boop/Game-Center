@echo off
title Game Center - EXE Build
python -m pip install --upgrade pip
python -m pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "Game Center" tb_builder.py
echo.
echo Fertig. Die EXE liegt im Ordner dist.
pause
