#!/usr/bin/env python3
"""
Football Betting Analysis Bot - Main Entry Point

Telegram-бот для анализа футбольных матчей и рекомендаций по ставкам.
Анализирует форму команд, статистику и генерирует прогнозы.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

def check_environment():
    """Проверяет наличие необходимых переменных окружения"""
    load_dotenv()
    
    required_vars = ['TELEGRAM_BOT_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Отсутствуют обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Создайте файл .env на основе .env.example")
        print("   или установите переменные окружения вручную.")
        return False
    
    return True

def show_help():
    """Показывает справку по использованию"""
    help_text = """
🏆 Football Betting Analysis Bot

Использование:
    python main.py          - Запуск бота в обычном режиме
    python main.py --demo   - Запуск в демо-режиме (с тестовыми данными)
    python main.py --help   - Показать эту справку

Требования:
    1. Токен Telegram-бота (получить у @BotFather)
    2. API ключ для футбольных данных (опционально)
    3. Python 3.8+

Установка зависимостей:
    pip install -r requirements.txt

Настройка:
    1. Скопируйте .env.example в .env
    2. Заполните ваш TELEGRAM_BOT_TOKEN
    3. Опционально добавьте FOOTBALL_API_KEY

Команды бота:
    /start   - Главное меню
    /matches - Анализ матчей на завтра
    /today   - Анализ матчей на сегодня
    /help    - Помощь
    """
    print(help_text)

async def run_demo():
    """Запускает демо-версию бота с тестовыми данными"""
    print("🚀 Запуск бота в демо-режиме...")
    print("📊 Будут использоваться тестовые данные")
    
    try:
        from demo import DemoBettingBot
        bot = DemoBettingBot()
        await bot.run_demo()
    except ImportError:
        print("❌ Демо-модуль не найден. Создайте demo.py")
    except Exception as e:
        print(f"❌ Ошибка запуска демо: {e}")

def run_bot():
    """Запускает полную версию бота"""
    if not check_environment():
        return
    
    print("🚀 Запуск Football Betting Bot...")
    
    try:
        from bot import FootballBettingBot
        bot = FootballBettingBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
            return
        elif arg in ['--demo', '-d', 'demo']:
            asyncio.run(run_demo())
            return
        else:
            print(f"❌ Неизвестный аргумент: {arg}")
            print("Используйте --help для справки")
            return
    
    # Обычный запуск
    run_bot()

if __name__ == "__main__":
    main()