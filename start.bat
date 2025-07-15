@echo off
chcp 65001 > nul
echo =============================================
echo VK Bot Automation - Запуск
echo =============================================
echo.

rem Проверка наличия Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8 или выше
    echo Скачать: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem Проверка наличия основных файлов
if not exist "vk_bot_gui.py" (
    echo ❌ Файл vk_bot_gui.py не найден!
    pause
    exit /b 1
)

if not exist ".env" (
    echo ⚠️ Файл .env не найден!
    echo Запускаю установку...
    python install.py
    pause
    exit /b 1
)

echo 🚀 Запуск VK Bot Automation...
echo.

rem Запуск приложения
python run.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска приложения
    echo Попробуйте запустить: python install.py
    pause
)

echo.
echo Работа завершена.
pause