#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import re
import time
import logging
from typing import Optional, Dict, List, Tuple
from pyrogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup

logger = logging.getLogger(__name__)

class BotInterface:
    """Класс для работы с интерфейсом Telegram бота"""
    
    @staticmethod
    def parse_task_message(message_text: str) -> Dict[str, str]:
        """Парсинг сообщения с заданием от бота"""
        result = {
            'task_type': None,
            'url': None,
            'reward': None,
            'description': '',
            'time_limit': None
        }
        
        if not message_text:
            return result
        
        text_lower = message_text.lower()
        
        # Определение типа задания
        if any(word in text_lower for word in ['репост', 'repost', 'поделиться']):
            result['task_type'] = 'repost'
        elif any(word in text_lower for word in ['лайк', 'like', 'нравится']):
            result['task_type'] = 'like'
        elif any(word in text_lower for word in ['комментарий', 'comment', 'комент']):
            result['task_type'] = 'comment'
        
        # Извлечение URL
        url_patterns = [
            r'https://vk\.com/[^\s\)]+',
            r'https://m\.vk\.com/[^\s\)]+',
            r'vk\.com/[^\s\)]+',
            r'https://vkontakte\.ru/[^\s\)]+'
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, message_text)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                result['url'] = url
                break
        
        # Извлечение информации о вознаграждении
        reward_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:руб|₽|рублей?)',
            r'от\s+(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*р'
        ]
        
        for pattern in reward_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['reward'] = match.group(1).replace(',', '.')
                break
        
        # Извлечение времени выполнения
        time_patterns = [
            r'(\d+)\s*(?:секунд|сек)',
            r'(\d+)\s*(?:минут|мин)',
            r'выполнение\s+дается\s+(\d+)'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['time_limit'] = match.group(1)
                break
        
        result['description'] = message_text
        return result
    
    @staticmethod
    def extract_buttons_text(message: Message) -> List[str]:
        """Извлечение текста кнопок из сообщения"""
        buttons = []
        
        if hasattr(message, 'reply_markup') and message.reply_markup:
            if hasattr(message.reply_markup, 'inline_keyboard'):
                # Inline кнопки
                for row in message.reply_markup.inline_keyboard:
                    for button in row:
                        if hasattr(button, 'text'):
                            buttons.append(button.text)
            elif hasattr(message.reply_markup, 'keyboard'):
                # Reply кнопки
                for row in message.reply_markup.keyboard:
                    for button in row:
                        if hasattr(button, 'text'):
                            buttons.append(button.text)
        
        return buttons
    
    @staticmethod
    def find_earn_button_text(buttons: List[str]) -> Optional[str]:
        """Поиск текста кнопки 'Заработать'"""
        earn_keywords = ['заработать', 'earn', '💰', 'работа', 'задания']
        
        for button_text in buttons:
            text_lower = button_text.lower()
            for keyword in earn_keywords:
                if keyword in text_lower:
                    return button_text
        
        return None
    
    @staticmethod
    def find_get_task_button_text(buttons: List[str]) -> Optional[str]:
        """Поиск текста кнопки 'Получить задание'"""
        task_keywords = ['получить задание', 'get task', 'задание', 'новое задание']
        
        for button_text in buttons:
            text_lower = button_text.lower()
            for keyword in task_keywords:
                if keyword in text_lower:
                    return button_text
        
        return None
    
    @staticmethod
    def find_complete_button_text(buttons: List[str]) -> Optional[str]:
        """Поиск текста кнопки 'Выполнил'"""
        complete_keywords = ['выполнил', 'completed', 'готово', 'done', 'сделал']
        
        for button_text in buttons:
            text_lower = button_text.lower()
            for keyword in complete_keywords:
                if keyword in text_lower:
                    return button_text
        
        return None
    
    @staticmethod
    def find_check_button_text(buttons: List[str]) -> Optional[str]:
        """Поиск текста кнопки 'Проверить задание'"""
        check_keywords = ['проверить', 'check', 'проверка']
        
        for button_text in buttons:
            text_lower = button_text.lower()
            for keyword in check_keywords:
                if keyword in text_lower:
                    return button_text
        
        return None

class VKUrlProcessor:
    """Класс для обработки VK URL"""
    
    @staticmethod
    def normalize_vk_url(url: str) -> str:
        """Нормализация VK URL"""
        if not url:
            return url
        
        # Удаление параметров из URL
        if '?' in url:
            url = url.split('?')[0]
        
        # Замена мобильной версии на обычную
        url = url.replace('m.vk.com', 'vk.com')
        
        # Добавление https если отсутствует
        if not url.startswith('http'):
            url = 'https://' + url
        
        return url
    
    @staticmethod
    def extract_post_id(url: str) -> Optional[Tuple[str, str]]:
        """Извлечение ID поста из URL"""
        patterns = [
            r'vk\.com/wall(-?\d+)_(\d+)',
            r'vk\.com/[^/]+\?w=wall(-?\d+)_(\d+)',
            r'vk\.com/.*wall(-?\d+)_(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner_id = match.group(1)
                post_id = match.group(2)
                return owner_id, post_id
        
        return None
    
    @staticmethod
    def is_valid_vk_url(url: str) -> bool:
        """Проверка валидности VK URL"""
        if not url:
            return False
        
        vk_patterns = [
            r'vk\.com/',
            r'vkontakte\.ru/',
            r'm\.vk\.com/'
        ]
        
        return any(re.search(pattern, url) for pattern in vk_patterns)

class TaskValidator:
    """Класс для валидации заданий"""
    
    @staticmethod
    def is_valid_task(task_data: Dict[str, str]) -> bool:
        """Проверка валидности задания"""
        required_fields = ['task_type', 'url']
        
        for field in required_fields:
            if not task_data.get(field):
                return False
        
        # Проверка типа задания
        valid_types = ['like', 'repost', 'comment']
        if task_data['task_type'] not in valid_types:
            return False
        
        # Проверка URL
        if not VKUrlProcessor.is_valid_vk_url(task_data['url']):
            return False
        
        return True
    
    @staticmethod
    def estimate_task_complexity(task_data: Dict[str, str]) -> str:
        """Оценка сложности задания"""
        task_type = task_data.get('task_type', '')
        
        complexity_map = {
            'like': 'easy',
            'repost': 'medium',
            'comment': 'hard'
        }
        
        return complexity_map.get(task_type, 'unknown')

class MessageProcessor:
    """Класс для обработки сообщений бота"""
    
    @staticmethod
    async def wait_for_specific_message(client, bot_username: str, 
                                      keywords: List[str], 
                                      timeout: int = 30) -> Optional[Message]:
        """Ожидание конкретного сообщения от бота"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                messages = []
                async for message in client.get_chat_history(bot_username, limit=5):
                    messages.append(message)
                
                for message in messages:
                    if (message.from_user and 
                        message.from_user.username == bot_username and
                        message.text):
                        
                        text_lower = message.text.lower()
                        if any(keyword.lower() in text_lower for keyword in keywords):
                            return message
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка при ожидании сообщения: {e}")
                await asyncio.sleep(1)
        
        return None
    
    @staticmethod
    def extract_error_info(message_text: str) -> Optional[Dict[str, str]]:
        """Извлечение информации об ошибке из сообщения"""
        if not message_text:
            return None
        
        text_lower = message_text.lower()
        error_patterns = {
            'insufficient_funds': ['недостаточно средств', 'нет денег', 'insufficient funds'],
            'task_expired': ['задание истекло', 'время вышло', 'task expired'],
            'already_completed': ['уже выполнено', 'already completed'],
            'invalid_action': ['неверное действие', 'invalid action'],
            'rate_limit': ['слишком быстро', 'rate limit', 'подождите']
        }
        
        for error_type, patterns in error_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return {
                    'type': error_type,
                    'message': message_text
                }
        
        return None

class CommentGenerator:
    """Класс для генерации комментариев"""
    
    @staticmethod
    def generate_comment(post_content: str = "", task_type: str = "comment") -> str:
        """Генерация комментария"""
        positive_comments = [
            "Интересно! 👍",
            "Классно! 😊",
            "Супер! ✨",
            "Отлично! 👌",
            "Круто! 🔥",
            "Замечательно! 💯",
            "Здорово! 🎉",
            "Прекрасно! ❤️",
            "Awesome! 👏",
            "Great! 🌟"
        ]
        
        neutral_comments = [
            "Спасибо за пост!",
            "Полезная информация",
            "Интересная тема",
            "Хорошо написано",
            "Познавательно",
            "Актуально",
            "Благодарю!",
            "Хорошая подача материала"
        ]
        
        import random
        
        # Выбираем тип комментария в зависимости от содержания
        if len(post_content) > 100:
            # Для длинных постов - более нейтральные комментарии
            return random.choice(neutral_comments)
        else:
            # Для коротких постов - более эмоциональные
            return random.choice(positive_comments)
    
    @staticmethod
    def generate_relevant_comment(post_text: str) -> str:
        """Генерация релевантного комментария на основе содержания поста"""
        if not post_text:
            return CommentGenerator.generate_comment()
        
        text_lower = post_text.lower()
        
        # Тематические комментарии
        thematic_comments = {
            'спорт': ["Отличная мотивация! 💪", "Спорт - это жизнь! 🏃‍♂️"],
            'музыка': ["Классная музыка! 🎵", "Отличный трек! 🎧"],
            'фото': ["Красивое фото! 📸", "Отличный кадр! 👌"],
            'еда': ["Выглядит аппетитно! 😋", "Вкусно! 🍽️"],
            'путешествия': ["Красивые места! ✈️", "Хочется туда! 🌍"],
            'новости': ["Интересные новости", "Актуальная информация"],
            'юмор': ["Смешно! 😄", "Хорошая шутка! 😂"]
        }
        
        for theme, comments in thematic_comments.items():
            if theme in text_lower:
                import random
                return random.choice(comments)
        
        return CommentGenerator.generate_comment(post_text)