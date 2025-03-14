@echo off
REM 若無虛擬環境，則建立 venv
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM 升級 pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM 安裝必要套件（若已安裝則會略過）
echo Installing required packages...
python -m pip install pyinstaller tkinter-tooltip ttkbootstrap tktooltip pyperclip pillow pywin32 gpxpy pyproj pydub opencv-python numpy ffmpeg-python

echo Running MNYA_WordCodeGen.py...
python MNYA_WordCodeGen.py

pause
