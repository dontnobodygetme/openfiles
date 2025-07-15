#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой запускаемый файл для VK Bot Automation
"""

import sys
import os
from pathlib import Path

def check_requirements():
    """Проверка наличия необходимых зависимостей"""
    required_modules = [
        'tkinter', 'pyrogram', 'selenium', 'vk_api', 
        'dotenv', 'fake_useragent', 'undetected_chromedriver'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            if module == 'tkinter':
                import tkinter
            elif module == 'pyrogram':
                import pyrogram
            elif module == 'selenium':
                import selenium
            elif module == 'vk_api':
                import vk_api
            elif module == 'dotenv':
                import dotenv
            elif module == 'fake_useragent':
                import fake_useragent
            elif module == 'undetected_chromedriver':
                import undetected_chromedriver
        except ImportError:
            missing_modules.append(module)
    
    return missing_modules

def install_requirements():
    """Установка отсутствующих зависимостей"""
    import subprocess
    
    print("Установка зависимостей...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Зависимости установлены успешно!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def check_config():
    """Проверка конфигурации"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️ Файл .env не найден!")
        print("Создайте файл .env на основе .env.example")
        
        if Path(".env.example").exists():
            print("Скопируйте .env.example в .env и заполните настройки")
        
        return False
    
    return True

def main():
    """Главная функция"""
    print("🚀 VK Bot Automation - Запуск приложения")
    print("=" * 50)
    
    # Проверка зависимостей
    missing = check_requirements()
    if missing:
        print(f"❌ Отсутствуют модули: {', '.join(missing)}")
        
        response = input("Установить автоматически? (y/n): ")
        if response.lower() in ['y', 'yes', 'да']:
            if not install_requirements():
                print("Не удалось установить зависимости. Установите вручную:")
                print("pip install -r requirements.txt")
                return
        else:
            print("Установите зависимости вручную:")
            print("pip install -r requirements.txt")
            return
    
    # Проверка конфигурации
    if not check_config():
        return
    
    # Запуск GUI приложения
    try:
        print("🎮 Запуск GUI приложения...")
        
        # Импорт и запуск GUI
        from vk_bot_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все файлы находятся в одной папке")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()