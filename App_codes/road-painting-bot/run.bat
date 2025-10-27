@echo off
REM Quick start script for Road Painting Bot (Windows)

echo ==================================
echo Road Painting Bot - Quick Start
echo ==================================
echo.

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo Created .env file
    echo Please edit .env and add your TELEGRAM_BOT_TOKEN
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo Dependencies installed
echo.

REM Run the bot
echo Starting bot...
echo ==================================
echo.
python bot.py

pause
