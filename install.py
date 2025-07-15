#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт установки и настройки VK Bot Automation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Печать баннера"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    VK Bot Automation                          ║
║                   Установка и настройка                       ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    
    print(f"✅ Python версия: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    
    try:
        # Обновление pip
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        
        # Установка зависимостей
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        
        print("✅ Зависимости установлены успешно!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки: {e}")
        return False
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден")
        return False

def setup_config():
    """Настройка конфигурации"""
    print("\n⚙️ Настройка конфигурации...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ Файл .env уже существует")
        
        overwrite = input("Перезаписать? (y/n): ")
        if overwrite.lower() not in ['y', 'yes', 'да']:
            return True
    
    if not env_example.exists():
        print("❌ Файл .env.example не найден")
        return False
    
    # Копирование примера конфигурации
    shutil.copy(env_example, env_file)
    print(f"✅ Создан файл .env из {env_example}")
    
    return True

def configure_env():
    """Интерактивная настройка .env файла"""
    print("\n🔧 Настройка переменных окружения...")
    
    # Чтение текущего .env файла
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Файл .env не найден")
        return False
    
    print("\nВведите настройки (оставьте пустым для пропуска):")
    
    # Настройки для ввода
    settings = {
        'API_ID': 'Telegram API ID',
        'API_HASH': 'Telegram API Hash',
        'PHONE_NUMBER': 'Номер телефона (+7xxxxxxxxxx)',
        'BOT_USERNAME': 'Username бота (по умолчанию: Vsem_Platit_bot)',
        'VK_ACCESS_TOKEN': 'VK токен (опционально)',
        'TASK_DELAY': 'Задержка между заданиями в секундах (по умолчанию: 20)',
        'HEADLESS': 'Скрытый режим браузера (True/False, по умолчанию: False)'
    }
    
    # Чтение текущих настроек
    current_settings = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                current_settings[key] = value
    
    # Обновление настроек
    updated_settings = current_settings.copy()
    
    for key, description in settings.items():
        current_value = current_settings.get(key, '')
        if current_value and not current_value.startswith('your_'):
            prompt = f"{description} [текущее: {current_value}]: "
        else:
            prompt = f"{description}: "
        
        new_value = input(prompt).strip()
        if new_value:
            updated_settings[key] = new_value
    
    # Запись обновленных настроек
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# VK Bot Automation - Конфигурация\n\n")
        
        f.write("# Telegram API настройки\n")
        f.write(f"API_ID={updated_settings.get('API_ID', 'your_api_id_here')}\n")
        f.write(f"API_HASH={updated_settings.get('API_HASH', 'your_api_hash_here')}\n")
        f.write(f"PHONE_NUMBER={updated_settings.get('PHONE_NUMBER', '+7xxxxxxxxxx')}\n\n")
        
        f.write("# Настройки бота\n")
        f.write(f"BOT_USERNAME={updated_settings.get('BOT_USERNAME', 'Vsem_Platit_bot')}\n\n")
        
        f.write("# VK API токен (опционально)\n")
        f.write(f"VK_ACCESS_TOKEN={updated_settings.get('VK_ACCESS_TOKEN', 'your_vk_token_here')}\n\n")
        
        f.write("# Настройки автоматизации\n")
        f.write(f"HEADLESS={updated_settings.get('HEADLESS', 'False')}\n")
        f.write(f"TASK_DELAY={updated_settings.get('TASK_DELAY', '20')}\n")
        f.write(f"RETRY_DELAY={updated_settings.get('RETRY_DELAY', '5')}\n")
        f.write(f"MAX_RETRIES={updated_settings.get('MAX_RETRIES', '3')}\n")
    
    print("✅ Конфигурация обновлена!")
    return True

def test_installation():
    """Тестирование установки"""
    print("\n🧪 Тестирование установки...")
    
    try:
        # Проверка импорта основных модулей
        import tkinter
        import pyrogram
        import selenium
        import vk_api
        import dotenv
        
        print("✅ Все модули импортированы успешно!")
        
        # Проверка файлов
        required_files = ['vk_bot_gui.py', 'vk_bot_automation.py', '.env']
        missing_files = [f for f in required_files if not Path(f).exists()]
        
        if missing_files:
            print(f"⚠️ Отсутствуют файлы: {', '.join(missing_files)}")
            return False
        
        print("✅ Все необходимые файлы найдены!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    """Главная функция установки"""
    print_banner()
    
    # Проверка версии Python
    if not check_python_version():
        return
    
    # Установка зависимостей
    if not install_requirements():
        print("\n❌ Установка прервана из-за ошибок")
        return
    
    # Настройка конфигурации
    if not setup_config():
        print("\n❌ Ошибка настройки конфигурации")
        return
    
    # Интерактивная настройка
    configure_env_choice = input("\nНастроить переменные окружения сейчас? (y/n): ")
    if configure_env_choice.lower() in ['y', 'yes', 'да']:
        configure_env()
    
    # Тестирование
    if test_installation():
        print("\n🎉 Установка завершена успешно!")
        print("\nДля запуска приложения выполните:")
        print("python run.py")
        print("\nИли запустите GUI напрямую:")
        print("python vk_bot_gui.py")
    else:
        print("\n⚠️ Установка завершена с предупреждениями")
        print("Проверьте конфигурацию перед запуском")
    
    print("\n📖 Прочитайте README.md для подробных инструкций")

if __name__ == "__main__":
    main()