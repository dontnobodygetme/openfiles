#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import re
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
import vk_api
from fake_useragent import UserAgent

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VKTaskAutomation:
    """Класс для автоматизации выполнения заданий в ВК"""
    
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone_number = os.getenv('PHONE_NUMBER')
        self.bot_username = os.getenv('BOT_USERNAME', 'Vsem_Platit_bot')
        self.vk_token = os.getenv('VK_ACCESS_TOKEN')
        
        self.headless = os.getenv('HEADLESS', 'False').lower() == 'true'
        self.task_delay = int(os.getenv('TASK_DELAY', 20))
        self.retry_delay = int(os.getenv('RETRY_DELAY', 5))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        
        self.client = None
        self.driver = None
        self.vk_session = None
        self.vk = None
        self.current_task = None
        self.is_running = False
        self.gui_callback = None  # Callback для обновления GUI
        
    async def init_telegram_client(self):
        """Инициализация Telegram клиента"""
        try:
            self.client = Client(
                "vk_task_bot",
                api_id=self.api_id,
                api_hash=self.api_hash,
                phone_number=self.phone_number
            )
            await self.client.start()
            logger.info("Telegram клиент успешно запущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram клиента: {e}")
            return False
    
    def init_vk_session(self):
        """Инициализация VK API сессии"""
        try:
            if self.vk_token:
                self.vk_session = vk_api.VkApi(token=self.vk_token)
                self.vk = self.vk_session.get_api()
                logger.info("VK API сессия успешно инициализирована")
                return True
            else:
                logger.warning("VK токен не найден, будет использоваться только браузер")
                return False
        except Exception as e:
            logger.error(f"Ошибка инициализации VK API: {e}")
            return False
    
    def init_browser(self):
        """Инициализация браузера"""
        try:
            chrome_options = Options()
            ua = UserAgent()
            
            chrome_options.add_argument(f'--user-agent={ua.random}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                chrome_options.add_argument('--headless')
                
            # Использование undetected-chromedriver для обхода защиты
            self.driver = uc.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Браузер успешно запущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {e}")
            return False
    
    async def send_message_to_bot(self, message: str):
        """Отправка сообщения боту"""
        try:
            await self.client.send_message(self.bot_username, message)
            logger.info(f"Отправлено сообщение боту: {message}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения боту: {e}")
            return False
    
    async def get_bot_messages(self, limit: int = 10) -> List[Message]:
        """Получение последних сообщений от бота"""
        try:
            messages = []
            async for message in self.client.get_chat_history(self.bot_username, limit=limit):
                messages.append(message)
            return messages
        except Exception as e:
            logger.error(f"Ошибка получения сообщений от бота: {e}")
            return []
    
    def extract_vk_url(self, text: str) -> Optional[str]:
        """Извлечение VK ссылки из текста"""
        vk_patterns = [
            r'https://vk\.com/[^\s]+',
            r'https://m\.vk\.com/[^\s]+',
            r'vk\.com/[^\s]+',
            r'https://vkontakte\.ru/[^\s]+'
        ]
        
        for pattern in vk_patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(0)
                if not url.startswith('http'):
                    url = 'https://' + url
                return url
        return None
    
    def determine_task_type(self, text: str) -> Optional[str]:
        """Определение типа задания"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['репост', 'repost', 'поделиться', 'share']):
            return 'repost'
        elif any(word in text_lower for word in ['лайк', 'like', 'нравится', 'класс']):
            return 'like'
        elif any(word in text_lower for word in ['комментарий', 'comment', 'комент', 'написать']):
            return 'comment'
        
        return None
    
    async def perform_vk_like(self, url: str) -> bool:
        """Выполнение лайка в ВК"""
        try:
            logger.info(f"Выполняю лайк: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Поиск кнопки лайка
            like_selectors = [
                "button[aria-label*='Нравится']",
                "button[aria-label*='Like']",
                ".PostButtonReactions__button",
                ".like_btn",
                "[data-reaction-button-type='like']",
                ".PostBottomAction--withText.PostBottomAction"
            ]
            
            for selector in like_selectors:
                try:
                    like_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    like_button.click()
                    logger.info("Лайк успешно поставлен")
                    time.sleep(2)
                    return True
                except TimeoutException:
                    continue
            
            logger.warning("Кнопка лайка не найдена")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении лайка: {e}")
            return False
    
    async def perform_vk_repost(self, url: str) -> bool:
        """Выполнение репоста в ВК"""
        try:
            logger.info(f"Выполняю репост: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Поиск кнопки репоста
            repost_selectors = [
                "button[aria-label*='Поделиться']",
                "button[aria-label*='Share']",
                ".PostButtonReactions__button--share",
                ".share_btn",
                "[data-reaction-button-type='share']"
            ]
            
            for selector in repost_selectors:
                try:
                    repost_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    repost_button.click()
                    time.sleep(2)
                    
                    # Подтверждение репоста
                    confirm_selectors = [
                        "button[data-testid='share-post-button']",
                        ".FlatButton--primary",
                        ".button_blue"
                    ]
                    
                    for confirm_selector in confirm_selectors:
                        try:
                            confirm_button = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, confirm_selector))
                            )
                            confirm_button.click()
                            logger.info("Репост успешно выполнен")
                            time.sleep(2)
                            return True
                        except TimeoutException:
                            continue
                            
                except TimeoutException:
                    continue
            
            logger.warning("Кнопка репоста не найдена")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении репоста: {e}")
            return False
    
    async def perform_vk_comment(self, url: str, comment_text: str = "Интересно! 👍") -> bool:
        """Выполнение комментария в ВК"""
        try:
            logger.info(f"Оставляю комментарий: {url}")
            
            self.driver.get(url)
            time.sleep(3)
            
            # Поиск поля комментария
            comment_selectors = [
                "textarea[placeholder*='омментарий']",
                "textarea[placeholder*='comment']",
                ".reply_field",
                ".PostCommentsTextarea__textbox",
                ".comments_field"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_field = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    comment_field.click()
                    comment_field.send_keys(comment_text)
                    time.sleep(1)
                    
                    # Поиск кнопки отправки
                    send_selectors = [
                        "button[aria-label*='Отправить']",
                        "button[aria-label*='Send']",
                        ".reply_send",
                        ".FlatButton--primary"
                    ]
                    
                    for send_selector in send_selectors:
                        try:
                            send_button = self.driver.find_element(By.CSS_SELECTOR, send_selector)
                            send_button.click()
                            logger.info("Комментарий успешно оставлен")
                            time.sleep(2)
                            return True
                        except NoSuchElementException:
                            continue
                            
                except TimeoutException:
                    continue
            
            logger.warning("Поле комментария не найдено")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при оставлении комментария: {e}")
            return False
    
    async def process_task(self, task_url: str, task_type: str) -> bool:
        """Обработка задания"""
        try:
            logger.info(f"Обрабатываю задание: {task_type} для {task_url}")
            
            success = False
            if task_type == 'like':
                success = await self.perform_vk_like(task_url)
            elif task_type == 'repost':
                success = await self.perform_vk_repost(task_url)
            elif task_type == 'comment':
                success = await self.perform_vk_comment(task_url)
            else:
                logger.error(f"Неизвестный тип задания: {task_type}")
                success = False
            
            # Вызов callback для обновления GUI
            if self.gui_callback:
                self.gui_callback(task_type, success)
            
            return success
                
        except Exception as e:
            logger.error(f"Ошибка при обработке задания: {e}")
            if self.gui_callback:
                self.gui_callback(task_type, False)
            return False
    
    async def run_automation(self):
        """Основной цикл автоматизации"""
        logger.info("Запуск автоматизации...")
        self.is_running = True
        
        try:
            while self.is_running:
                # Отправляем команду "Заработать"
                await self.send_message_to_bot("💰 Заработать")
                await asyncio.sleep(2)
                
                # Получаем задание
                await self.send_message_to_bot("Получить задание")
                await asyncio.sleep(3)
                
                # Получаем последние сообщения от бота
                messages = await self.get_bot_messages(5)
                
                task_found = False
                for message in messages:
                    if message.from_user and message.from_user.username == self.bot_username:
                        message_text = message.text or ""
                        
                        # Ищем ссылку и определяем тип задания
                        task_url = self.extract_vk_url(message_text)
                        task_type = self.determine_task_type(message_text)
                        
                        if task_url and task_type:
                            logger.info(f"Найдено задание: {task_type} - {task_url}")
                            
                            # Выполняем задание
                            success = await self.process_task(task_url, task_type)
                            
                            if success:
                                # Отмечаем задание как выполненное
                                await asyncio.sleep(self.task_delay)
                                await self.send_message_to_bot("Выполнил")
                                await asyncio.sleep(3)
                                
                                # Проверяем задание
                                await self.send_message_to_bot("Проверить задание")
                                await asyncio.sleep(5)
                                
                                logger.info("Задание выполнено и отправлено на проверку")
                            else:
                                logger.error("Не удалось выполнить задание")
                                await self.send_message_to_bot("Пропустить")
                            
                            task_found = True
                            break
                
                if not task_found:
                    logger.info("Задания не найдены, ожидание...")
                    await asyncio.sleep(30)
                
                # Пауза между циклами
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Автоматизация остановлена пользователем")
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")
        finally:
            self.is_running = False
    
    async def start(self):
        """Запуск всех компонентов"""
        try:
            # Инициализация всех компонентов
            if not await self.init_telegram_client():
                return False
            
            if not self.init_browser():
                return False
            
            self.init_vk_session()
            
            # Запуск автоматизации
            await self.run_automation()
            
        except Exception as e:
            logger.error(f"Ошибка при запуске: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Браузер закрыт")
            
            if self.client:
                await self.client.stop()
                logger.info("Telegram клиент остановлен")
                
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}")

async def main():
    """Главная функция"""
    automation = VKTaskAutomation()
    await automation.start()

if __name__ == "__main__":
    asyncio.run(main())