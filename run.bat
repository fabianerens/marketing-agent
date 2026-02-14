@echo off
REM Quick start script for YouTube Marketing Agent (Windows)

echo 🎬 YouTube Marketing Agent
echo ==========================
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  No .env file found!
    echo Creating from .env.example...
    copy .env.example .env >nul
    echo.
    echo ✓ Created .env file
    echo.
    echo 📝 NEXT STEPS:
    echo 1. Edit .env and add your API keys:
    echo    - YOUTUBE_API_KEY
    echo    - GOOGLE_API_KEY
    echo 2. Run this script again
    echo.
    exit /b 1
)

REM Create data directory
if not exist data mkdir data

echo 🚀 Starting application...
echo.

REM Check for uv
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    uv run python -m app.gradio_app
) else (
    REM Check for virtual environment
    if exist .venv\Scripts\activate.bat (
        call .venv\Scripts\activate.bat
        python -m app.gradio_app
    ) else (
        echo ⚠️  No virtual environment found
        echo.
        echo Creating virtual environment and installing dependencies...
        python -m venv .venv
        call .venv\Scripts\activate.bat
        pip install -e .
        echo.
        echo ✓ Dependencies installed
        echo.
        echo 🚀 Starting application...
        python -m app.gradio_app
    )
)
