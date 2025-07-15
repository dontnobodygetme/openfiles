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
for f in os.listdir(pyrogram_path):
    if f.endswith('.py'):
        a.datas += [(f'pyrogram{os.sep}{f}', os.path.join(pyrogram_path, f), 'DATA')]
    elif os.path.isdir(os.path.join(pyrogram_path, f)) and not f.startswith('__pycache__'):
        # Добавляем только подкаталоги, исключая __pycache__
        for root, dirs, files in os.walk(os.path.join(pyrogram_path, f)):
            # Исключаем __pycache__ из директорий
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, pyrogram_path)
                    a.datas += [(f'pyrogram{os.sep}{rel_path}', full_path, 'DATA')]

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