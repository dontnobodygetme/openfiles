#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """Сборка exe файла с помощью PyInstaller с правильными настройками для pyrogram"""
    
    print("Сборка VK Bot Automation в exe файл...")
    
    # Проверка установки PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller версия: {PyInstaller.__version__}")
    except ImportError:
        print("Установка PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Параметры сборки
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    # Очистка предыдущих сборок
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Создание spec файла с правильными настройками для pyrogram
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['vk_bot_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.env.example', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        # Pyrogram и его зависимости
        'pyrogram',
        'pyrogram.client',
        'pyrogram.filters',
        'pyrogram.types',
        'pyrogram.errors',
        'pyrogram.handlers',
        'pyrogram.methods',
        'pyrogram.raw',
        'pyrogram.utils',
        'pyrogram.storage',
        'pyrogram.session',
        'pyaes',
        'pysocks',
        'tgcrypto',
        
        # Selenium и его зависимости  
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        'undetected_chromedriver',
        
        # VK API
        'vk_api',
        'requests',
        'urllib3',
        
        # Web scraping
        'beautifulsoup4',
        'bs4',
        'lxml',
        'fake_useragent',
        
        # GUI и системные модули
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'threading',
        'asyncio',
        'json',
        'logging',
        'datetime',
        'time',
        'os',
        'sys',
        're',
        
        # Дополнительные зависимости
        'python_dotenv',
        'dotenv',
        'typing',
        'pathlib',
        'collections',
        'functools',
        'itertools',
        'hashlib',
        'base64',
        'hmac',
        'struct',
        'socket',
        'ssl',
        'http',
        'urllib',
        'certifi',
        'charset_normalizer',
        'idna'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'IPython',
        'jupyter',
        'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Добавляем специальные пути для pyrogram
import pyrogram
pyrogram_path = os.path.dirname(pyrogram.__file__)
a.datas += [(f'pyrogram{os.sep}{f}', os.path.join(pyrogram_path, f), 'DATA') 
           for f in os.listdir(pyrogram_path) 
           if f.endswith('.py') or os.path.isdir(os.path.join(pyrogram_path, f))]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VK_Bot_Automation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Отключаем UPX для лучшей совместимости
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version='version.txt' if os.path.exists('version.txt') else None,
)
"""
    
    # Запись spec файла
    with open("vk_bot_automation_fixed.spec", "w", encoding="utf-8") as f:
        f.write(spec_content.strip())
    
    # Команда сборки
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--log-level=DEBUG",  # Добавляем отладочную информацию
        "vk_bot_automation_fixed.spec"
    ]
    
    print(f"Запуск команды: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Сборка завершена успешно!")
        print(f"Исполняемый файл: {dist_dir / 'VK_Bot_Automation.exe'}")
        
        # Копирование дополнительных файлов
        if Path(".env.example").exists():
            shutil.copy(".env.example", dist_dir / ".env.example")
        
        if Path("README.md").exists():
            shutil.copy("README.md", dist_dir / "README.md")
        
        print("\nДополнительные файлы скопированы в папку dist/")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка сборки: {e}")
        return False
    
    return True

def install_build_dependencies():
    """Установка зависимостей для сборки"""
    print("Установка зависимостей для сборки...")
    
    build_deps = [
        "pyinstaller>=5.0",
        "setuptools",
        "wheel"
    ]
    
    for dep in build_deps:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--break-system-packages", dep
            ])
        except subprocess.CalledProcessError as e:
            print(f"Ошибка установки {dep}: {e}")
            return False
    
    return True

def create_version_file():
    """Создание файла версии для Windows exe"""
    version_content = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'VK Bot Automation'),
        StringStruct(u'FileDescription', u'Автоматизация заданий VK через Telegram бота'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'VK_Bot_Automation'),
        StringStruct(u'LegalCopyright', u'© 2024'),
        StringStruct(u'OriginalFilename', u'VK_Bot_Automation.exe'),
        StringStruct(u'ProductName', u'VK Bot Automation'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    with open("version.txt", "w", encoding="utf-8") as f:
        f.write(version_content.strip())
    
    print("Файл версии создан: version.txt")

def test_imports():
    """Тестирование импортов перед сборкой"""
    print("Тестирование импортов...")
    
    # Список модулей с альтернативными именами
    required_modules = [
        ('pyrogram', 'pyrogram'),
        ('selenium', 'selenium'), 
        ('vk_api', 'vk_api'),
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),  # beautifulsoup4 импортируется как bs4
        ('lxml', 'lxml'),
        ('fake_useragent', 'fake_useragent'),
        ('undetected_chromedriver', 'undetected_chromedriver'),
        ('python_dotenv', 'dotenv'),  # python_dotenv импортируется как dotenv
        ('tgcrypto', 'tgcrypto')
    ]
    
    failed_imports = []
    
    for package_name, import_name in required_modules:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError as e:
            print(f"❌ {package_name}: {e}")
            failed_imports.append(package_name)
    
    if failed_imports:
        print(f"\n❌ Не удалось импортировать: {', '.join(failed_imports)}")
        return False
    
    print("\n✅ Все необходимые модули доступны")
    return True

def main():
    """Главная функция"""
    print("=== VK Bot Automation Builder (Fixed) ===\n")
    
    # Проверка наличия основных файлов
    required_files = ["vk_bot_gui.py", "vk_bot_automation.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        return
    
    # Тестирование импортов
    if not test_imports():
        print("\n❌ Установите недостающие зависимости:")
        print("pip install --break-system-packages -r requirements.txt")
        return
    
    # Установка зависимостей для сборки
    if not install_build_dependencies():
        print("\n❌ Ошибка установки зависимостей для сборки")
        return
    
    # Создание файла версии
    create_version_file()
    
    # Сборка exe
    if build_exe():
        print("\n🎉 Готово! Ваше приложение собрано и готово к использованию.")
        print("\nИнструкции по использованию:")
        print("1. Скопируйте .env.example в .env и заполните настройки")
        print("2. Запустите VK_Bot_Automation.exe")
        print("3. Нажмите 'Запустить' для начала автоматизации")
        print("\n📁 Найти файл: dist/VK_Bot_Automation.exe")
    else:
        print("\n❌ Сборка не удалась. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()