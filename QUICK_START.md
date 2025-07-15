# 🚀 Быстрый старт VK Bot Automation

## Для пользователей Windows (exe файл)

1. **Скачайте** готовый `VK_Bot_Automation.exe`
2. **Создайте** файл `.env` рядом с exe файлом
3. **Заполните** `.env` файл:
   ```env
   API_ID=ваш_api_id
   API_HASH=ваш_api_hash
   PHONE_NUMBER=+7xxxxxxxxxx
   BOT_USERNAME=Vsem_Platit_bot
   ```
4. **Запустите** `VK_Bot_Automation.exe`
5. **Нажмите** кнопку "Запустить"

## Для разработчиков (из исходного кода)

### Быстрая установка
```bash
# 1. Клонируйте репозиторий
git clone <repository_url>
cd vk-bot-automation

# 2. Запустите установку
python install.py

# 3. Запустите приложение
python run.py
```

### Альтернативный способ
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка конфигурации
cp .env.example .env
# Отредактируйте .env файл

# Запуск GUI
python vk_bot_gui.py
```

## 📝 Получение Telegram API

1. Перейдите на https://my.telegram.org
2. Войдите с номером телефона
3. Откройте "API development tools"
4. Создайте приложение
5. Скопируйте `API_ID` и `API_HASH`

## 🎮 Использование

1. **Запустите** приложение
2. **Настройте** параметры в левой панели
3. **Нажмите** "Запустить" для автоматизации
4. **Мониторьте** статистику и логи
5. **Остановите** когда нужно

## ⚠️ Важно

- Не передавайте файл `.env` никому
- Используйте разумные задержки (20+ секунд)
- Соблюдайте правила VK и Telegram
- Следите за логами на предмет ошибок

## 🔧 Сборка exe (для разработчиков)

```bash
# Установите зависимости для сборки
pip install -r requirements_build.txt

# Запустите сборку
python build_exe.py

# Готовый exe будет в папке dist/
```

## 🐛 Проблемы?

1. **Ошибка импорта** → `python install.py`
2. **Нет .env файла** → Скопируйте из `.env.example`
3. **Браузер не запускается** → Установите Google Chrome
4. **Telegram не подключается** → Проверьте API_ID и API_HASH

Подробнее в `README.md`