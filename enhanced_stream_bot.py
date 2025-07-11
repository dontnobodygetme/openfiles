#!/usr/bin/env python3
"""
УЛУЧШЕННАЯ ВЕРСИЯ: Образовательный Telegram Bot для управления viewer симуляцией

⚠️ КРИТИЧЕСКИ ВАЖНО: Этот код предназначен ТОЛЬКО для:
- Образовательных целей
- Работы с собственными платформами
- Нагрузочного тестирования собственных сервисов
- Изучения принципов работы web-технологий

НЕ используйте на официальных платформах (Twitch, YouTube, etc.)
"""

import asyncio
import logging
import json
import sqlite3
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import aiohttp
from fake_useragent import UserAgent

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper())
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log_level,
    handlers=[
        logging.FileHandler('stream_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityManager:
    """Менеджер безопасности"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def get_authorized_users() -> Set[int]:
        """Получение списка авторизованных пользователей"""
        users_str = os.getenv('AUTHORIZED_USERS', '')
        if not users_str:
            logger.warning("⚠️ AUTHORIZED_USERS не настроен! Бот будет доступен всем!")
            return set()
        
        try:
            return {int(user_id.strip()) for user_id in users_str.split(',') if user_id.strip()}
        except ValueError:
            logger.error("❌ Неверный формат AUTHORIZED_USERS")
            return set()

class AccountManager:
    """Улучшенное управление аккаунтами"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'accounts.db')
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных с улучшенной структурой"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                cookies TEXT,
                user_agent TEXT,
                proxy TEXT,
                status TEXT DEFAULT 'active',
                last_used TIMESTAMP,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_id INTEGER,
                target_url TEXT NOT NULL,
                duration INTEGER,
                status TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")
    
    def add_account(self, username: str, password: str, proxy: str = None) -> bool:
        """Добавление аккаунта с хешированием пароля"""
        try:
            ua = UserAgent()
            password_hash = SecurityManager.hash_password(password)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (username, password_hash, user_agent, proxy)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, ua.random, proxy))
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Аккаунт {username} добавлен")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Аккаунт {username} уже существует")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении аккаунта: {e}")
            return False
    
    def get_active_accounts(self, limit: int = None) -> List[Dict]:
        """Получение активных аккаунтов с ограничением"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM accounts WHERE status = "active" ORDER BY success_count DESC'
        if limit:
            query += f' LIMIT {limit}'
            
        cursor.execute(query)
        accounts = []
        
        for row in cursor.fetchall():
            accounts.append({
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'cookies': row[3],
                'user_agent': row[4],
                'proxy': row[5],
                'status': row[6],
                'last_used': row[7],
                'success_count': row[8],
                'error_count': row[9]
            })
        
        conn.close()
        return accounts
    
    def update_account_stats(self, account_id: int, success: bool):
        """Обновление статистики аккаунта"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if success:
            cursor.execute('''
                UPDATE accounts 
                SET success_count = success_count + 1, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (account_id,))
        else:
            cursor.execute('''
                UPDATE accounts 
                SET error_count = error_count + 1
                WHERE id = ?
            ''', (account_id,))
            
        conn.commit()
        conn.close()
    
    def log_simulation(self, user_id: int, account_id: int, target_url: str, 
                      duration: int, status: str, error_message: str = None):
        """Логирование симуляции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO simulation_logs 
            (user_id, account_id, target_url, duration, status, error_message, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, account_id, target_url, duration, status, error_message))
        
        conn.commit()
        conn.close()

class ViewerSimulator:
    """Улучшенный симулятор просмотра с контролем ресурсов"""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = aiohttp.ClientTimeout(total=30)
        self.max_concurrent = int(os.getenv('MAX_CONCURRENT_SIMULATIONS', 50))
        self.max_duration = int(os.getenv('MAX_SIMULATION_DURATION', 300))
        
    async def simulate_viewer(self, account: Dict, stream_url: str, 
                            duration: int = None, user_id: int = None) -> bool:
        """
        Улучшенная симуляция просмотра с контролем ресурсов
        
        Args:
            account: Данные аккаунта
            stream_url: URL стрима (ТОЛЬКО ваша платформа!)
            duration: Длительность в секундах
            user_id: ID пользователя для логирования
        
        Returns:
            bool: Успешность симуляции
        """
        duration = min(duration or 300, self.max_duration)
        account_id = account['id']
        
        logger.info(f"🎓 ОБРАЗОВАТЕЛЬНАЯ ДЕМОНСТРАЦИЯ: Симуляция для {account['username']} на {duration}сек")
        
        start_time = time.time()
        success = False
        error_message = None
        
        try:
            # Проверка URL (базовая валидация)
            if not self._is_safe_url(stream_url):
                raise ValueError("Небезопасный или неподдерживаемый URL")
            
            headers = {
                'User-Agent': account['user_agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            # Добавляем cookies если есть
            cookies = {}
            if account['cookies']:
                try:
                    cookies = json.loads(account['cookies'])
                except json.JSONDecodeError:
                    logger.warning(f"Неверный формат cookies для {account['username']}")
            
            proxy = account['proxy'] if account['proxy'] else None
            
            async with aiohttp.ClientSession(
                timeout=self.session_timeout,
                headers=headers,
                cookies=cookies
            ) as session:
                
                # Основной запрос к стриму
                async with session.get(stream_url, proxy=proxy) as response:
                    if response.status == 200:
                        logger.info(f"✅ Подключение установлено для {account['username']}")
                        
                        # Симуляция активного просмотра с периодическими запросами
                        intervals = duration // 30  # Проверка каждые 30 сек
                        
                        for i in range(intervals):
                            await asyncio.sleep(30)
                            
                            # Периодический heartbeat запрос
                            try:
                                async with session.head(stream_url, proxy=proxy) as heartbeat:
                                    if heartbeat.status == 200:
                                        logger.info(f"📺 {account['username']} активен ({i+1}/{intervals})")
                                    else:
                                        logger.warning(f"⚠️ Heartbeat failed: {heartbeat.status}")
                            except Exception as e:
                                logger.warning(f"⚠️ Heartbeat error: {e}")
                        
                        success = True
                        logger.info(f"✅ Симуляция для {account['username']} завершена успешно")
                        
                    else:
                        error_message = f"HTTP {response.status}"
                        logger.warning(f"❌ Ошибка подключения: {response.status}")
                        
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Ошибка симуляции для {account['username']}: {e}")
        
        finally:
            # Логирование результата
            if user_id:
                AccountManager().log_simulation(
                    user_id, account_id, stream_url, duration, 
                    'success' if success else 'error', error_message
                )
            
            # Обновление статистики аккаунта
            AccountManager().update_account_stats(account_id, success)
            
            # Удаление из активных сессий
            session_key = f"{account_id}_{user_id}"
            self.active_sessions.pop(session_key, None)
        
        return success
    
    def _is_safe_url(self, url: str) -> bool:
        """Базовая проверка безопасности URL"""
        # Список запрещенных доменов (официальные платформы)
        forbidden_domains = [
            'twitch.tv', 'youtube.com', 'youtu.be', 'facebook.com',
            'instagram.com', 'tiktok.com', 'vk.com', 'ok.ru'
        ]
        
        url_lower = url.lower()
        for domain in forbidden_domains:
            if domain in url_lower:
                logger.error(f"❌ Запрещенный домен: {domain}")
                return False
        
        # Проверка протокола
        if not (url.startswith('http://') or url.startswith('https://')):
            logger.error("❌ Неподдерживаемый протокол")
            return False
        
        return True
    
    async def start_mass_simulation(self, accounts: List[Dict], stream_url: str, 
                                  user_id: int, duration: int = 300) -> Dict:
        """
        Запуск массовой симуляции с улучшенным контролем
        
        Returns:
            Dict: Статистика выполнения
        """
        duration = min(duration, self.max_duration)
        accounts = accounts[:self.max_concurrent]  # Ограничение количества
        
        logger.info(f"🚀 Запуск симуляции для {len(accounts)} аккаунтов (макс. {self.max_concurrent})")
        
        # Создание семафора для контроля нагрузки
        semaphore = asyncio.Semaphore(min(self.max_concurrent, 20))
        
        async def limited_simulation(account):
            async with semaphore:
                session_key = f"{account['id']}_{user_id}"
                self.active_sessions[session_key] = {
                    'account': account['username'],
                    'started': datetime.now(),
                    'url': stream_url
                }
                
                return await self.simulate_viewer(account, stream_url, duration, user_id)
        
        # Запуск симуляций с контролем ошибок
        tasks = [limited_simulation(account) for account in accounts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Подсчет статистики
        stats = {
            'total': len(accounts),
            'success': sum(1 for r in results if r is True),
            'failed': sum(1 for r in results if r is False),
            'errors': sum(1 for r in results if isinstance(r, Exception)),
            'duration': duration
        }
        
        logger.info(f"📊 Статистика: {stats['success']} успешных, {stats['failed']} неудачных, {stats['errors']} ошибок")
        return stats

class EnhancedStreamBot:
    """Улучшенная версия Telegram бота с безопасностью"""
    
    def __init__(self, token: str):
        self.token = token
        self.account_manager = AccountManager()
        self.viewer_simulator = ViewerSimulator()
        self.authorized_users = SecurityManager.get_authorized_users()
        self.user_states = {}  # Состояния пользователей
        
        if not self.authorized_users:
            logger.warning("⚠️ Список авторизованных пользователей пуст!")
    
    def check_authorization(self, user_id: int) -> bool:
        """Проверка авторизации пользователя"""
        if not self.authorized_users:
            return True  # Если список пуст, разрешаем всем (для демо)
        return user_id in self.authorized_users
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start с проверкой авторизации"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text(
                "❌ У вас нет доступа к этому боту.\n"
                "Обратитесь к администратору для получения доступа."
            )
            logger.warning(f"🚫 Неавторизованная попытка доступа от {user_id}")
            return
        
        welcome_text = f"""
🎓 ОБРАЗОВАТЕЛЬНЫЙ STREAM BOT v2.0

👋 Добро пожаловать, {update.effective_user.first_name}!

⚠️ КРИТИЧЕСКИЕ ПРЕДУПРЕЖДЕНИЯ:
• Используйте ТОЛЬКО на собственных платформах
• НЕ используйте на Twitch, YouTube и других официальных сервисах
• Может нарушать Terms of Service

📊 Ваша статистика:
• ID: {user_id}
• Авторизован: ✅
• Активных аккаунтов: {len(self.account_manager.get_active_accounts())}

Доступные команды:
/accounts - Управление аккаунтами
/simulate - Запуск симуляции (ТОЛЬКО для ваших платформ!)
/status - Статус системы
/logs - Просмотр логов
/help - Помощь
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Аккаунты", callback_data="accounts"),
             InlineKeyboardButton("🎮 Симуляция", callback_data="simulate")],
            [InlineKeyboardButton("📊 Статус", callback_data="status"),
             InlineKeyboardButton("📄 Логи", callback_data="logs")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода в зависимости от состояния пользователя"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            return
        
        user_state = self.user_states.get(user_id)
        
        if user_state == "waiting_for_url":
            stream_url = update.message.text.strip()
            
            # Валидация URL
            if not stream_url.startswith(('http://', 'https://')):
                await update.message.reply_text("❌ URL должен начинаться с http:// или https://")
                return
            
            # Проверка на запрещенные домены
            if not self.viewer_simulator._is_safe_url(stream_url):
                await update.message.reply_text(
                    "❌ Обнаружен запрещенный домен!\n\n"
                    "⚠️ Используйте ТОЛЬКО собственные платформы:\n"
                    "• НЕ Twitch.tv\n"
                    "• НЕ YouTube.com\n"
                    "• НЕ Facebook, Instagram, TikTok\n\n"
                    "Попробуйте снова с URL вашей платформы."
                )
                return
            
            # Сохраняем URL и переходим к выбору параметров
            self.user_states[user_id] = {"state": "configuring", "url": stream_url}
            
            accounts_count = len(self.account_manager.get_active_accounts())
            
            keyboard = [
                [InlineKeyboardButton("🎯 Быстрый старт (5 мин)", callback_data="quick_start")],
                [InlineKeyboardButton("⚙️ Настроить параметры", callback_data="configure_sim")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ URL принят: {stream_url}\n\n"
                f"📊 Доступно аккаунтов: {accounts_count}\n"
                f"🎯 Выберите режим запуска:",
                reply_markup=reply_markup
            )
        
        else:
            await update.message.reply_text(
                "❓ Неожиданный ввод. Используйте команды или кнопки."
            )

def main():
    """Запуск улучшенного бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в переменных окружения")
        print("Создайте файл .env на основе .env.example")
        return
    
    # Создаем экземпляр бота
    bot = EnhancedStreamBot(token)
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_input))
    # application.add_handler(CallbackQueryHandler(bot.button_handler))  # Будет добавлен в полной версии
    
    logger.info("🚀 Запуск улучшенного образовательного Stream Bot v2.0...")
    logger.warning("⚠️ Используйте ТОЛЬКО для образовательных целей и собственных платформ!")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()