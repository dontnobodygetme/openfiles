#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """Сборка exe файла с помощью PyInstaller"""
    
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
    
    # Создание spec файла
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
        'pyrogram',
        'selenium',
        'vk_api',
        'undetected_chromedriver',
        'fake_useragent',
        'tkinter',
        'asyncio',
        'threading'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

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
    upx=True,
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
    with open("vk_bot_automation.spec", "w", encoding="utf-8") as f:
        f.write(spec_content.strip())
    
    # Команда сборки
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "vk_bot_automation.spec"
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

def main():
    """Главная функция"""
    print("=== VK Bot Automation Builder ===\n")
    
    # Проверка наличия основных файлов
    required_files = ["vk_bot_gui.py", "vk_bot_automation.py"]
    missing_files = [f for f in required_files if not Path(f).exists()]
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
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
    else:
        print("\n❌ Сборка не удалась. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()