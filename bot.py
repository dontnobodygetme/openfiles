import logging
import asyncio
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)
from dotenv import load_dotenv

from football_api import FootballAPI, FreeFootballAPI
from analyzer import FootballAnalyzer

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FootballBettingBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = os.getenv('ADMIN_USER_ID')
        
        # Инициализируем API и анализатор
        try:
            self.api = FootballAPI()
        except:
            # Если основной API недоступен, используем тестовый
            self.api = FreeFootballAPI()
            logger.warning("Using mock API data")
        
        self.analyzer = FootballAnalyzer(self.api)
        
        # Хранилище для пользовательских настроек
        self.user_preferences = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        welcome_message = f"""
🏆 Добро пожаловать в Football Betting Analyzer, {user.first_name}!

Этот бот анализирует футбольные матчи и предоставляет рекомендации по ставкам.

🔹 /matches - Получить анализ матчей на завтра
🔹 /today - Матчи на сегодня
🔹 /settings - Настройки бота
🔹 /help - Помощь

Бот анализирует:
• Форма команд (последние 5 матчей)
• Турнирную таблицу
• Статистику личных встреч
• Домашнее преимущество
• Статистику голов

⚠️ Помните: ставки сопряжены с риском. Играйте ответственно!
        """
        
        keyboard = [
            [InlineKeyboardButton("⚽️ Матчи на завтра", callback_data="tomorrow_matches")],
            [InlineKeyboardButton("📅 Матчи на сегодня", callback_data="today_matches")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📚 Помощь по использованию бота:

🔸 *Основные команды:*
/start - Главное меню
/matches - Анализ матчей на завтра
/today - Анализ матчей на сегодня
/settings - Настройки бота

🔸 *Как читать анализ:*
🏠 - Домашняя команда
✈️ - Гостевая команда
📊 - Форма команды (% от максимума)
🎯 - Вероятность события
⭐ - Уровень уверенности в прогнозе

🔸 *Типы ставок:*
• Исход матча (1X2)
• Тотал голов (больше/меньше 2.5)
• Обе забьют (да/нет)

🔸 *Факторы анализа:*
• Последние 5 матчей команды
• Статистика личных встреч
• Домашнее преимущество
• Средняя результативность

⚠️ Бот предоставляет аналитическую информацию. Принятие решений о ставках остается на ваше усмотрение.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def get_matches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /matches"""
        await self.send_matches_analysis(update, context, days_ahead=1)
    
    async def get_today_matches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /today"""
        await self.send_matches_analysis(update, context, days_ahead=0)
    
    async def send_matches_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE, days_ahead: int = 1):
        """Отправляет анализ матчей"""
        chat_id = update.effective_chat.id
        
        # Отправляем сообщение о загрузке
        loading_msg = await context.bot.send_message(
            chat_id, 
            "🔄 Анализирую матчи... Это может занять несколько секунд."
        )
        
        try:
            # Получаем матчи
            if hasattr(self.api, 'get_mock_data'):
                matches = await self.api.get_mock_data()
            else:
                matches = await self.api.get_upcoming_matches(days_ahead)
            
            if not matches:
                await loading_msg.edit_text("❌ Матчи не найдены на указанную дату.")
                return
            
            # Анализируем первые 5 матчей (чтобы не перегружать API)
            analyzed_matches = []
            for i, match in enumerate(matches[:5]):
                try:
                    analysis = await self.analyzer.analyze_match(match)
                    analyzed_matches.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing match {i}: {e}")
                    continue
            
            if not analyzed_matches:
                await loading_msg.edit_text("❌ Не удалось проанализировать матчи.")
                return
            
            # Удаляем сообщение о загрузке
            await loading_msg.delete()
            
            # Отправляем результаты анализа
            date_str = "сегодня" if days_ahead == 0 else "завтра"
            header = f"⚽️ *Анализ матчей на {date_str}*\n\n"
            
            for analysis in analyzed_matches:
                match_text = self.format_match_analysis(analysis)
                full_message = header + match_text
                
                keyboard = [
                    [InlineKeyboardButton("📊 Подробная статистика", 
                                        callback_data=f"details_{analysis['match']['id']}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id, 
                    full_message, 
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
                
                # Небольшая пауза между сообщениями
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Error in send_matches_analysis: {e}")
            await loading_msg.edit_text(f"❌ Произошла ошибка: {e}")
    
    def format_match_analysis(self, analysis: Dict) -> str:
        """Форматирует анализ матча для отправки"""
        match = analysis['match']
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        
        # Время матча
        match_time = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
        time_str = match_time.strftime('%H:%M')
        
        # Основная информация
        text = f"🏟 *{home_team} vs {away_team}*\n"
        text += f"🕐 Время: {time_str}\n"
        text += f"🏆 Лига: {match.get('competition', {}).get('name', 'N/A')}\n\n"
        
        # Форма команд
        home_form = analysis['home_form']
        away_form = analysis['away_form']
        
        text += f"📊 *Форма команд:*\n"
        text += f"🏠 {home_team}: {home_form['form_score']}% "
        text += f"({home_form['wins']}П-{home_form['draws']}Н-{home_form['losses']}П)\n"
        text += f"✈️ {away_team}: {away_form['form_score']}% "
        text += f"({away_form['wins']}П-{away_form['draws']}Н-{away_form['losses']}П)\n\n"
        
        # Анализ вероятностей
        betting = analysis['betting_analysis']
        text += f"🎯 *Вероятности:*\n"
        text += f"🏠 Победа {home_team}: {betting['team1_win_prob']}%\n"
        text += f"✈️ Победа {away_team}: {betting['team2_win_prob']}%\n"
        text += f"🤝 Ничья: {betting['draw_prob']}%\n"
        text += f"⚽️ Тотал >2.5: {betting['over_2_5_prob']}%\n"
        text += f"🎯 Обе забьют: {betting['btts_prob']}%\n\n"
        
        # Рекомендации
        if analysis['recommendations']:
            text += f"💡 *Рекомендации:*\n"
            for rec in analysis['recommendations']:
                text += f"• {rec}\n"
        else:
            text += f"💡 *Рекомендации:* Матч сложно прогнозируемый\n"
        
        # Уверенность
        confidence = analysis['confidence_score']
        text += f"\n⭐ Уверенность в прогнозе: {confidence}%"
        
        return text
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "tomorrow_matches":
            await self.send_matches_analysis(update, context, days_ahead=1)
        elif data == "today_matches":
            await self.send_matches_analysis(update, context, days_ahead=0)
        elif data == "settings":
            await self.show_settings(update, context)
        elif data.startswith("details_"):
            match_id = data.split("_")[1]
            await query.edit_message_text("📊 Подробная статистика пока в разработке!")
    
    async def show_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает настройки бота"""
        settings_text = """
⚙️ *Настройки бота*

🔹 Автоматические уведомления: Выкл
🔹 Часовой пояс: UTC
🔹 Любимые лиги: Все
🔹 Минимальная уверенность: 60%

_Функции настроек будут добавлены в следующих версиях_
        """
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                settings_text, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                settings_text, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
    
    def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return
        
        # Создаем приложение
        app = Application.builder().token(self.token).build()
        
        # Добавляем обработчики
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("matches", self.get_matches_command))
        app.add_handler(CommandHandler("today", self.get_today_matches_command))
        app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Добавляем обработчик ошибок
        app.add_error_handler(self.error_handler)
        
        logger.info("Bot started successfully!")
        
        # Запускаем бота
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = FootballBettingBot()
    bot.run()