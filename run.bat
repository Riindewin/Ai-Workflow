@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Ultimate Image Converter AI v2.0.0

:: Python kurulu mu kontrol et
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [HATA] Python bulunamadi!
    echo.
    echo Lutfen Python'u indirip kurun:
    echo https://www.python.org/downloads/
    echo.
    echo Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

echo Python bulundu.
echo Bagimliliklar kontrol ediliyor...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

echo.
echo Uygulama baslatiliyor...
python app.py
if errorlevel 1 (
    echo.
    echo [HATA] Uygulama beklenmedik sekilde kapandi.
    pause
)
