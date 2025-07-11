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
/help - Помощь
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Аккаунты", callback_data="accounts"),
             InlineKeyboardButton("🎮 Симуляция", callback_data="simulate")],
            [InlineKeyboardButton("📊 Статус", callback_data="status"),
             InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def accounts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда управления аккаунтами"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text("❌ У вас нет доступа к этому боту")
            return
        
        accounts = self.account_manager.get_active_accounts()
        
        text = f"📋 УПРАВЛЕНИЕ АККАУНТАМИ\n\n"
        text += f"📊 Всего аккаунтов: {len(accounts)}\n"
        text += f"⚡ Максимум одновременно: {self.viewer_simulator.max_concurrent}\n\n"
        
        if accounts:
            text += "👥 Последние аккаунты:\n"
            for i, acc in enumerate(accounts[:5], 1):
                success_rate = 0
                if acc['success_count'] + acc['error_count'] > 0:
                    success_rate = (acc['success_count'] / (acc['success_count'] + acc['error_count'])) * 100
                
                text += f"{i}. {acc['username']} "
                text += f"(✅{acc['success_count']} ❌{acc['error_count']} "
                text += f"📈{success_rate:.1f}%)\n"
            
            if len(accounts) > 5:
                text += f"... и еще {len(accounts) - 5} аккаунтов\n"
        else:
            text += "Аккаунты еще не добавлены"
        
        text += "\n⚠️ Используйте только для собственных платформ!"
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить аккаунт", callback_data="add_account")],
            [InlineKeyboardButton("📋 Показать все", callback_data="list_accounts")],
            [InlineKeyboardButton("🧹 Очистить все", callback_data="clear_accounts")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
    
    async def simulate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда запуска симуляции"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text("❌ У вас нет доступа к этому боту")
            return
        
        accounts = self.account_manager.get_active_accounts()
        
        if not accounts:
            await update.message.reply_text(
                "❌ Нет доступных аккаунтов для симуляции!\n\n"
                "Сначала добавьте аккаунты через команду /accounts"
            )
            return
        
        warning_text = f"""
⚠️ КРИТИЧЕСКИЕ ПРЕДУПРЕЖДЕНИЯ:

1. Используйте ТОЛЬКО на СОБСТВЕННЫХ платформах!
2. НЕ используйте на Twitch.tv, YouTube или других официальных сервисах
3. Это может привести к блокировке аккаунтов
4. Убедитесь, что у вас есть права на тестирование целевой платформы

📊 Доступно аккаунтов: {len(accounts)}
⚡ Максимум одновременно: {min(len(accounts), self.viewer_simulator.max_concurrent)}

Продолжить только если это ВАША платформа:
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Это МОЯ платформа", callback_data="confirm_simulation")],
            [InlineKeyboardButton("❌ Отмена", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(warning_text, reply_markup=reply_markup)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда статуса системы"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text("❌ У вас нет доступа к этому боту")
            return
        
        accounts = self.account_manager.get_active_accounts()
        active_sessions = len(self.viewer_simulator.active_sessions)
        
        # Статистика аккаунтов
        total_success = sum(acc['success_count'] for acc in accounts)
        total_errors = sum(acc['error_count'] for acc in accounts)
        
        status_text = f"""
📊 СТАТУС СИСТЕМЫ

👥 Аккаунты:
• Всего: {len(accounts)}
• Активных сессий: {active_sessions}
• Успешных операций: {total_success}
• Ошибок: {total_errors}

⚙️ Система:
• Максимум одновременно: {self.viewer_simulator.max_concurrent}
• Максимальная длительность: {self.viewer_simulator.max_duration}с
• Статус: ✅ Работает

⚠️ Используйте ответственно!
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="status")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(status_text, reply_markup=reply_markup)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if not self.check_authorization(user_id):
            await query.edit_message_text("❌ У вас нет доступа к этому боту")
            return
        
        data = query.data
        
        # Главное меню
        if data == "main_menu":
            await self.start_command(update, context)
        
        # Управление аккаунтами
        elif data == "accounts":
            await self.accounts_command(update, context)
        
        elif data == "add_account":
            self.user_states[user_id] = "waiting_for_account"
            await query.edit_message_text(
                "➕ ДОБАВЛЕНИЕ АККАУНТА\n\n"
                "Отправьте данные аккаунта в формате:\n"
                "`логин:пароль`\n\n"
                "Пример: `myuser123:mypassword456`\n\n"
                "⚠️ ВАЖНО: Добавляйте только аккаунты для собственных платформ!\n\n"
                "Отправьте /cancel для отмены"
            )
        
        elif data == "list_accounts":
            accounts = self.account_manager.get_active_accounts()
            
            if not accounts:
                text = "📋 Список аккаунтов пуст"
            else:
                text = f"📋 ВСЕ АККАУНТЫ ({len(accounts)})\n\n"
                for i, acc in enumerate(accounts, 1):
                    success_rate = 0
                    total_ops = acc['success_count'] + acc['error_count']
                    if total_ops > 0:
                        success_rate = (acc['success_count'] / total_ops) * 100
                    
                    last_used = acc['last_used'] or "Никогда"
                    if acc['last_used']:
                        last_used = "Недавно"
                    
                    text += f"{i}. **{acc['username']}**\n"
                    text += f"   ✅ Успешно: {acc['success_count']}\n"
                    text += f"   ❌ Ошибок: {acc['error_count']}\n"
                    text += f"   📈 Успешность: {success_rate:.1f}%\n"
                    text += f"   🕒 Последнее использование: {last_used}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить аккаунт", callback_data="add_account")],
                [InlineKeyboardButton("🔙 Назад", callback_data="accounts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup)
        
        elif data == "clear_accounts":
            keyboard = [
                [InlineKeyboardButton("✅ Да, очистить ВСЕ", callback_data="confirm_clear")],
                [InlineKeyboardButton("❌ Отмена", callback_data="accounts")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚠️ ВНИМАНИЕ!\n\n"
                "Вы действительно хотите удалить ВСЕ аккаунты?\n"
                "Это действие нельзя отменить!",
                reply_markup=reply_markup
            )
        
        elif data == "confirm_clear":
            # Очистка всех аккаунтов
            import os
            if os.path.exists(self.account_manager.db_path):
                conn = sqlite3.connect(self.account_manager.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM accounts")
                conn.commit()
                conn.close()
            
            await query.edit_message_text(
                "✅ Все аккаунты удалены!\n\n"
                "Теперь можно добавить новые аккаунты.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Добавить аккаунт", callback_data="add_account")],
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
                ])
            )
        
        # Симуляция
        elif data == "simulate":
            await self.simulate_command(update, context)
        
        elif data == "confirm_simulation":
            self.user_states[user_id] = "waiting_for_url"
            await query.edit_message_text(
                "🌐 ВВЕДИТЕ URL СТРИМА\n\n"
                "Отправьте URL вашей платформы для тестирования:\n"
                "Пример: `https://your-platform.com/stream/gena_gensh`\n\n"
                "⚠️ ТОЛЬКО для собственных платформ!\n"
                "НЕ Twitch, YouTube, Facebook и т.д.\n\n"
                "Отправьте /cancel для отмены"
            )
        
        # Выбор количества зрителей
        elif data.startswith("viewers_"):
            viewer_count = int(data.split("_")[1])
            user_state = self.user_states.get(user_id, {})
            user_state["viewer_count"] = viewer_count
            self.user_states[user_id] = user_state
            
            keyboard = [
                [InlineKeyboardButton("🚀 ЗАПУСТИТЬ", callback_data="start_simulation")],
                [InlineKeyboardButton("🔢 Изменить количество", callback_data="change_viewers")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Параметры симуляции:\n\n"
                f"🌐 URL: {user_state.get('url', 'Не указан')}\n"
                f"👥 Количество зрителей: {viewer_count}\n"
                f"⏱️ Длительность: 5 минут\n\n"
                f"⚠️ ВНИМАНИЕ: Убедитесь, что это ваша платформа!",
                reply_markup=reply_markup
            )
        
        elif data == "custom_viewers":
            user_state = self.user_states.get(user_id, {})
            user_state["state"] = "waiting_custom_viewers"
            self.user_states[user_id] = user_state
            
            accounts_count = len(self.account_manager.get_active_accounts())
            max_viewers = min(accounts_count, self.viewer_simulator.max_concurrent)
            
            await query.edit_message_text(
                f"� УКАЖИТЕ КОЛИЧЕСТВО ЗРИТЕЛЕЙ\n\n"
                f"Введите число от 1 до {max_viewers}\n\n"
                f"📊 Доступно аккаунтов: {accounts_count}\n"
                f"⚡ Максимум системы: {self.viewer_simulator.max_concurrent}\n\n"
                f"Отправьте /cancel для отмены"
            )
        
        elif data == "change_viewers":
            user_state = self.user_states.get(user_id, {})
            url = user_state.get('url', '')
            
            # Возвращаемся к выбору количества зрителей
            self.user_states[user_id] = {"state": "selecting_viewers", "url": url}
            
            accounts_count = len(self.account_manager.get_active_accounts())
            max_viewers = min(accounts_count, self.viewer_simulator.max_concurrent)
            
            keyboard = [
                [InlineKeyboardButton(f"👥 Все ({accounts_count})", callback_data=f"viewers_{accounts_count}")],
                [InlineKeyboardButton(f"🎯 Половина ({accounts_count//2})", callback_data=f"viewers_{accounts_count//2}")],
                [InlineKeyboardButton(f"� Максимум ({max_viewers})", callback_data=f"viewers_{max_viewers}")],
                [InlineKeyboardButton("🔢 Указать количество", callback_data="custom_viewers")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"👥 Выберите количество зрителей:\n\n"
                f"📊 Доступно аккаунтов: {accounts_count}\n"
                f"⚡ Максимум одновременно: {max_viewers}",
                reply_markup=reply_markup
            )
        
        elif data == "start_simulation":
            user_state = self.user_states.get(user_id, {})
            url = user_state.get('url')
            viewer_count = user_state.get('viewer_count')
            
            if not url or not viewer_count:
                await query.edit_message_text("❌ Ошибка: неполные данные для симуляции")
                return
            
            # Запуск симуляции
            await query.edit_message_text(
                f"🚀 ЗАПУСК СИМУЛЯЦИИ...\n\n"
                f"🌐 URL: {url}\n"
                f"👥 Зрителей: {viewer_count}\n"
                f"⏱️ Длительность: 5 минут\n\n"
                f"📊 Симуляция запущена в фоновом режиме.\n"
                f"Используйте /status для отслеживания прогресса."
            )
            
            # Получаем аккаунты для симуляции
            accounts = self.account_manager.get_active_accounts(limit=viewer_count)
            
            # Запускаем симуляцию в фоне
            asyncio.create_task(self._run_simulation_background(user_id, accounts, url, query.message.chat_id, context))
            
            # Сбрасываем состояние
            self.user_states.pop(user_id, None)
        
        # Статус
        elif data == "status":
            await self.status_command(update, context)
        
        # Помощь
        elif data == "help":
            help_text = """
❓ ПОМОЩЬ

Этот бот создан для образовательных целей и тестирования СОБСТВЕННЫХ платформ.

🔸 /start - Главное меню
🔸 /accounts - Управление аккаунтами
🔸 /simulate - Запуск симуляции
🔸 /status - Статус системы

📋 Добавление аккаунтов:
Используйте формат: логин:пароль
Пример: user123:pass456

⚠️ ВАЖНО:
• НЕ используйте на официальных платформах
• Может нарушать Terms of Service
• Используйте только на собственных сервисах
• Для образовательных целей

💡 Рекомендации:
• Создавайте качественный контент
• Используйте легальные методы продвижения
• Взаимодействуйте с реальной аудиторией
            """
            
            keyboard = [
                [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(help_text, reply_markup=reply_markup)
        
        # Отмена
        elif data == "cancel":
            self.user_states.pop(user_id, None)
            await query.edit_message_text(
                "❌ Операция отменена",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
                ])
            )
    
    async def _run_simulation_background(self, user_id: int, accounts: list, url: str, chat_id: int, context):
        """Запуск симуляции в фоновом режиме с уведомлением о результатах"""
        try:
            stats = await self.viewer_simulator.start_mass_simulation(accounts, url, user_id, 300)
            
            # Отправка результатов
            result_text = f"""
✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА

📊 Результаты:
• Всего запущено: {stats['total']}
• Успешно: {stats['success']}
• Неудачно: {stats['failed']}
• Ошибок: {stats['errors']}
• Длительность: {stats['duration']}с

🌐 URL: {url}
            """
            
            # Отправляем результат в чат
            await context.bot.send_message(chat_id=chat_id, text=result_text)
            
        except Exception as e:
            logger.error(f"Ошибка в фоновой симуляции: {e}")
            error_text = f"❌ Ошибка при выполнении симуляции: {str(e)}"
            await context.bot.send_message(chat_id=chat_id, text=error_text)
    
    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстового ввода в зависимости от состояния пользователя"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            return
        
        user_state = self.user_states.get(user_id)
        text = update.message.text.strip()
        
        # Обработка добавления аккаунта в формате логин:пароль
        if user_state == "waiting_for_account":
            if ":" not in text:
                await update.message.reply_text(
                    "❌ Неверный формат!\n\n"
                    "Используйте формат: `логин:пароль`\n"
                    "Пример: `myuser123:mypassword456`\n\n"
                    "Или отправьте /cancel для отмены"
                )
                return
            
            try:
                username, password = text.split(":", 1)
                username = username.strip()
                password = password.strip()
                
                if not username or not password:
                    await update.message.reply_text("❌ Логин и пароль не могут быть пустыми!")
                    return
                
                # Добавляем аккаунт
                success = self.account_manager.add_account(username, password)
                
                if success:
                    accounts_count = len(self.account_manager.get_active_accounts())
                    await update.message.reply_text(
                        f"✅ Аккаунт `{username}` успешно добавлен!\n\n"
                        f"📊 Всего аккаунтов: {accounts_count}\n\n"
                        "Хотите добавить еще один аккаунт?",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ Добавить еще", callback_data="add_account")],
                            [InlineKeyboardButton("📋 Показать все", callback_data="list_accounts")],
                            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
                        ])
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Аккаунт `{username}` уже существует!\n"
                        "Попробуйте другой логин."
                    )
                
                # Сбрасываем состояние
                self.user_states.pop(user_id, None)
                
            except Exception as e:
                logger.error(f"Ошибка при добавлении аккаунта: {e}")
                await update.message.reply_text("❌ Произошла ошибка при добавлении аккаунта")
        
        # Обработка ввода URL стрима
        elif user_state == "waiting_for_url":
            stream_url = text
            
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
            
            # Сохраняем URL и переходим к выбору количества зрителей
            self.user_states[user_id] = {"state": "selecting_viewers", "url": stream_url}
            
            accounts_count = len(self.account_manager.get_active_accounts())
            max_viewers = min(accounts_count, self.viewer_simulator.max_concurrent)
            
            if accounts_count == 0:
                await update.message.reply_text(
                    "❌ Нет доступных аккаунтов!\n"
                    "Сначала добавьте аккаунты через команду /accounts"
                )
                self.user_states.pop(user_id, None)
                return
            
            keyboard = [
                [InlineKeyboardButton(f"👥 Все ({accounts_count})", callback_data=f"viewers_{accounts_count}")],
                [InlineKeyboardButton(f"🎯 Половина ({accounts_count//2})", callback_data=f"viewers_{accounts_count//2}")],
                [InlineKeyboardButton(f"🔥 Максимум ({max_viewers})", callback_data=f"viewers_{max_viewers}")],
                [InlineKeyboardButton("🔢 Указать количество", callback_data="custom_viewers")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ URL принят: {stream_url}\n\n"
                f"📊 Доступно аккаунтов: {accounts_count}\n"
                f"⚡ Максимум одновременно: {max_viewers}\n\n"
                f"👥 Выберите количество зрителей:",
                reply_markup=reply_markup
            )
        
        # Обработка ввода пользовательского количества зрителей
        elif user_state and isinstance(user_state, dict) and user_state.get("state") == "waiting_custom_viewers":
            try:
                viewer_count = int(text)
                accounts_count = len(self.account_manager.get_active_accounts())
                max_viewers = min(accounts_count, self.viewer_simulator.max_concurrent)
                
                if viewer_count <= 0:
                    await update.message.reply_text("❌ Количество должно быть больше 0!")
                    return
                
                if viewer_count > max_viewers:
                    await update.message.reply_text(
                        f"❌ Максимально допустимое количество: {max_viewers}\n"
                        f"📊 Доступно аккаунтов: {accounts_count}\n"
                        f"⚡ Лимит системы: {self.viewer_simulator.max_concurrent}"
                    )
                    return
                
                # Сохраняем количество и показываем финальные параметры
                user_state["viewer_count"] = viewer_count
                self.user_states[user_id] = user_state
                
                keyboard = [
                    [InlineKeyboardButton("🚀 ЗАПУСТИТЬ", callback_data="start_simulation")],
                    [InlineKeyboardButton("⚙️ Изменить параметры", callback_data="change_params")],
                    [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ Параметры симуляции:\n\n"
                    f"🌐 URL: {user_state['url']}\n"
                    f"👥 Количество зрителей: {viewer_count}\n"
                    f"⏱️ Длительность: 5 минут\n\n"
                    f"⚠️ ВНИМАНИЕ: Убедитесь, что это ваша платформа!",
                    reply_markup=reply_markup
                )
                
            except ValueError:
                await update.message.reply_text("❌ Введите корректное число!")
        
        else:
            await update.message.reply_text(
                "❓ Неожиданный ввод. Используйте команды или кнопки.\n\n"
                "Доступные команды:\n"
                "/start - Главное меню\n"
                "/accounts - Управление аккаунтами\n"
                "/status - Статус системы\n"
                "/cancel - Отменить текущую операцию"
            )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда отмены текущей операции"""
        user_id = update.effective_user.id
        
        if not self.check_authorization(user_id):
            await update.message.reply_text("❌ У вас нет доступа к этому боту")
            return
        
        # Сбрасываем состояние пользователя
        self.user_states.pop(user_id, None)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ Операция отменена\n\n"
            "Все текущие действия прерваны.",
            reply_markup=reply_markup
        )

def main():
    """Запуск улучшенного бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("❌ Не найден TELEGRAM_BOT_TOKEN в переменных окружения")
        print("Создайте файл .env на основе .env.example")
        print("Добавьте ваш токен бота в файл .env:")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return
    
    # Создаем экземпляр бота
    bot = EnhancedStreamBot(token)
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("accounts", bot.accounts_command))
    application.add_handler(CommandHandler("simulate", bot.simulate_command))
    application.add_handler(CommandHandler("status", bot.status_command))
    application.add_handler(CommandHandler("cancel", bot.cancel_command))
    
    # Добавляем обработчик кнопок
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Добавляем обработчик текстовых сообщений (должен быть последним)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_input))
    
    logger.info("🚀 Запуск улучшенного образовательного Stream Bot v2.0...")
    logger.warning("⚠️ Используйте ТОЛЬКО для образовательных целей и собственных платформ!")
    
    # Выводим информацию о запуске
    print(f"🤖 Бот запущен успешно!")
    print(f"📋 Доступные команды:")
    print(f"   /start - Главное меню")
    print(f"   /accounts - Управление аккаунтами")
    print(f"   /simulate - Запуск симуляции")
    print(f"   /status - Статус системы")
    print(f"   /cancel - Отмена операции")
    print(f"\n⚠️  ВАЖНО: Используйте только для собственных платформ!")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()