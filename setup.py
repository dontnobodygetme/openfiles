#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Ваша версия: {sys.version}")
        return False
    print(f"✅ Python версия: {sys.version}")
    return True

def install_requirements():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def create_env_file():
    """Создание файла .env если он не существует"""
    if not os.path.exists('.env'):
        print("📝 Создание файла .env...")
        env_content = """# Telegram API (обязательно)
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+7XXXXXXXXXX

# VK API (опционально)
VK_ACCESS_TOKEN=your_vk_token_here

# Настройки бота
BOT_USERNAME=Vsem_Platit_bot
TARGET_BOT_USERNAME=Vsem_Platit_bot

# Настройки браузера
HEADLESS=False
CHROME_DRIVER_PATH=

# Задержки (секунды)
TASK_DELAY=20
RETRY_DELAY=5
MAX_RETRIES=3
"""
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Файл .env создан")
    else:
        print("✅ Файл .env уже существует")

def check_chrome():
    """Проверка наличия Chrome браузера"""
    print("🌐 Проверка Chrome браузера...")
    
    system = platform.system()
    chrome_paths = {
        'Windows': [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
        ],
        'Darwin': [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        ],
        'Linux': [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser'
        ]
    }
    
    if system in chrome_paths:
        for path in chrome_paths[system]:
            if os.path.exists(path):
                print(f"✅ Chrome найден: {path}")
                return True
    
    print("⚠️ Chrome браузер не найден")
    print("Пожалуйста, установите Google Chrome или Chromium")
    return False

def setup_instructions():
    """Вывод инструкций по настройке"""
    print("\n" + "="*50)
    print("🎯 ИНСТРУКЦИИ ПО НАСТРОЙКЕ")
    print("="*50)
    
    print("\n1️⃣ Получение Telegram API:")
    print("   • Перейдите на https://my.telegram.org/apps")
    print("   • Войдите в свой аккаунт Telegram")
    print("   • Создайте новое приложение")
    print("   • Скопируйте API ID и API Hash в .env файл")
    
    print("\n2️⃣ Настройка VK (опционально):")
    print("   • Перейдите на https://vkhost.github.io/")
    print("   • Получите токен доступа")
    print("   • Добавьте его в .env файл")
    
    print("\n3️⃣ Отредактируйте файл .env:")
    print("   • Замените your_api_id_here на ваш API ID")
    print("   • Замените your_api_hash_here на ваш API Hash")
    print("   • Укажите ваш номер телефона в международном формате")
    
    print("\n4️⃣ Запуск программы:")
    print("   python vk_bot_automation.py")
    
    print("\n⚠️ ВАЖНО:")
    print("   • Используйте программу ответственно")
    print("   • Соблюдайте ограничения сервисов")
    print("   • Проверяйте логи на наличие ошибок")

def main():
    """Основная функция установки"""
    print("🚀 Установка VK Task Bot Automation")
    print("="*40)
    
    # Проверка версии Python
    if not check_python_version():
        return False
    
    # Установка зависимостей
    if not install_requirements():
        return False
    
    # Создание .env файла
    create_env_file()
    
    # Проверка Chrome
    check_chrome()
    
    # Инструкции
    setup_instructions()
    
    print("\n✅ Установка завершена!")
    print("Теперь отредактируйте файл .env и запустите программу")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)