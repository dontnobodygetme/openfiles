#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe_simple():
    """Упрощенная сборка exe файла"""
    
    print("🔨 Простая сборка VK Bot Automation в exe файл...")
    
    # Проверка установки PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller версия: {PyInstaller.__version__}")
    except ImportError:
        print("📦 Установка PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Очистка предыдущих сборок
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("🗑️ Очищена папка build")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("🗑️ Очищена папка dist")
    
    # Проверка основных файлов
    if not Path("vk_bot_gui.py").exists():
        print("❌ Файл vk_bot_gui.py не найден!")
        return False
    
    if not Path("vk_bot_automation.py").exists():
        print("❌ Файл vk_bot_automation.py не найден!")
        return False
    
    print("✅ Основные файлы найдены")
    
    # Команда сборки PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",              # Один exe файл
        "--windowed",             # Без консоли
        "--name=VK_Bot_Automation",
        "--add-data=vk_bot_automation.py;.",  # Добавляем модуль автоматизации
        "--hidden-import=pyrogram",
        "--hidden-import=selenium",
        "--hidden-import=vk_api",
        "--hidden-import=undetected_chromedriver",
        "--hidden-import=fake_useragent",
        "--hidden-import=dotenv",
        "--hidden-import=tkinter",
        "--clean",
        "--noconfirm",
        "vk_bot_gui.py"
    ]
    
    print(f"🚀 Запуск команды сборки...")
    print(f"Команда: {' '.join(cmd[:5])}... (и дополнительные параметры)")
    
    try:
        # Запуск сборки
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Сборка завершена успешно!")
            
            # Проверка результата
            exe_file = dist_dir / "VK_Bot_Automation.exe"
            if exe_file.exists():
                file_size = exe_file.stat().st_size / (1024 * 1024)  # MB
                print(f"📦 Создан файл: {exe_file}")
                print(f"📏 Размер файла: {file_size:.1f} MB")
                
                # Создание примера конфигурации рядом с exe
                env_example_content = """# VK Bot Automation - Конфигурация
# Скопируйте этот файл в .env и заполните своими данными

# Telegram API настройки (обязательно)
# Получите на https://my.telegram.org
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+7xxxxxxxxxx

# Настройки бота
BOT_USERNAME=Vsem_Platit_bot

# VK API токен (опционально)
# Получите на https://vkhost.github.io/
VK_ACCESS_TOKEN=your_vk_token_here

# Настройки автоматизации
HEADLESS=False
TASK_DELAY=20
RETRY_DELAY=5
MAX_RETRIES=3
"""
                
                # Сохранение примера конфигурации
                with open(dist_dir / ".env.example", "w", encoding="utf-8") as f:
                    f.write(env_example_content)
                print("✅ Создан файл .env.example")
                
                # Создание инструкции
                readme_content = """# VK Bot Automation

## Быстрый старт:

1. Создайте файл .env рядом с этим exe файлом
2. Скопируйте содержимое из .env.example в .env
3. Заполните настройки в .env файле:
   - API_ID и API_HASH получите на https://my.telegram.org
   - Укажите ваш номер телефона в формате +7xxxxxxxxxx
4. Запустите VK_Bot_Automation.exe
5. Нажмите кнопку "Запустить"

## Важно:
- Установите Google Chrome браузер
- Не передавайте файл .env никому
- Используйте разумные задержки (20+ секунд)

Подробная документация: https://github.com/your-repo/
"""
                
                with open(dist_dir / "README.txt", "w", encoding="utf-8") as f:
                    f.write(readme_content)
                print("✅ Создан файл README.txt")
                
                return True
            else:
                print("❌ Exe файл не найден после сборки")
                return False
        else:
            print(f"❌ Ошибка сборки (код выхода: {result.returncode})")
            print("Вывод ошибки:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("🔧 VK Bot Automation - Простая сборка exe")
    print("=" * 60)
    
    # Проверка наличия основных файлов
    required_files = ["vk_bot_gui.py", "vk_bot_automation.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        return
    
    # Сборка
    if build_exe_simple():
        print("\n🎉 Сборка завершена успешно!")
        print("\n📋 Инструкции:")
        print("1. Перейдите в папку dist/")
        print("2. Скопируйте .env.example в .env")
        print("3. Заполните настройки в .env")
        print("4. Запустите VK_Bot_Automation.exe")
        print("\n📖 Прочитайте README.txt для подробностей")
    else:
        print("\n❌ Сборка не удалась.")
        print("💡 Попробуйте:")
        print("1. Обновить PyInstaller: pip install --upgrade pyinstaller")
        print("2. Установить зависимости: pip install -r requirements.txt")
        print("3. Перезапустить команду")

if __name__ == "__main__":
    main()