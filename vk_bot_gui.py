#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import time
from datetime import datetime
import json
import os
from typing import Dict, Optional
import logging

from vk_bot_automation import VKTaskAutomation

class VKBotGUI:
    """GUI приложение для автоматизации VK заданий через Telegram бота"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VK Bot Automation - @vsem_platit_bot")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Переменные состояния
        self.automation = None
        self.is_running = False
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'likes_count': 0,
            'reposts_count': 0,
            'comments_count': 0,
            'session_start': None,
            'last_task_time': None
        }
        
        # Загрузка статистики
        self.load_stats()
        
        # Настройка логирования
        self.setup_logging()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Обновление статистики каждую секунду
        self.update_stats_display()
    
    def setup_logging(self):
        """Настройка логирования для GUI"""
        self.log_handler = GUILogHandler(self)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Конфигурация сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="VK Bot Automation", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Левая панель - Управление
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Кнопки управления
        self.start_button = ttk.Button(control_frame, text="▶ Запустить", 
                                      command=self.start_automation,
                                      style="Success.TButton")
        self.start_button.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))
        
        self.stop_button = ttk.Button(control_frame, text="⏹ Остановить", 
                                     command=self.stop_automation,
                                     style="Danger.TButton",
                                     state="disabled")
        self.stop_button.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Статус
        self.status_label = ttk.Label(control_frame, text="Статус: Остановлен")
        self.status_label.grid(row=2, column=0, pady=(20, 5))
        
        # Индикатор работы
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Настройки
        settings_frame = ttk.LabelFrame(control_frame, text="Настройки", padding="5")
        settings_frame.grid(row=4, column=0, pady=(20, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(settings_frame, text="Задержка (сек):").grid(row=0, column=0, sticky=tk.W)
        self.delay_var = tk.StringVar(value="20")
        delay_entry = ttk.Entry(settings_frame, textvariable=self.delay_var, width=10)
        delay_entry.grid(row=0, column=1, padx=(5, 0))
        
        ttk.Label(settings_frame, text="Режим браузера:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.headless_var = tk.BooleanVar(value=False)
        headless_check = ttk.Checkbutton(settings_frame, text="Скрытый", 
                                        variable=self.headless_var)
        headless_check.grid(row=1, column=1, padx=(5, 0), pady=(5, 0))
        
        # Правая панель - Статистика и логи
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Статистика
        stats_frame = ttk.LabelFrame(right_frame, text="Статистика", padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        stats_frame.columnconfigure(1, weight=1)
        
        # Создание меток статистики
        self.stats_labels = {}
        stats_items = [
            ("Выполнено заданий:", "tasks_completed"),
            ("Неудачных заданий:", "tasks_failed"),
            ("Лайков:", "likes_count"),
            ("Репостов:", "reposts_count"),
            ("Комментариев:", "comments_count"),
            ("Время работы:", "session_time"),
            ("Последнее задание:", "last_task_time")
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            ttk.Label(stats_frame, text=label_text).grid(row=i, column=0, sticky=tk.W, pady=2)
            value_label = ttk.Label(stats_frame, text="0", font=("Arial", 9, "bold"))
            value_label.grid(row=i, column=1, sticky=tk.E, pady=2, padx=(10, 0))
            self.stats_labels[key] = value_label
        
        # Кнопка сброса статистики
        reset_button = ttk.Button(stats_frame, text="Сбросить статистику", 
                                 command=self.reset_stats)
        reset_button.grid(row=len(stats_items), column=0, columnspan=2, pady=(10, 0))
        
        # Логи
        logs_frame = ttk.LabelFrame(right_frame, text="Логи", padding="5")
        logs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=15, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка очистки логов
        clear_logs_button = ttk.Button(logs_frame, text="Очистить логи", 
                                      command=self.clear_logs)
        clear_logs_button.grid(row=1, column=0, pady=(5, 0))
        
        # Конфигурация весов
        control_frame.columnconfigure(0, weight=1)
        
        # Создание стилей
        self.create_styles()
    
    def create_styles(self):
        """Создание пользовательских стилей"""
        style = ttk.Style()
        
        # Стиль для кнопки запуска
        style.configure("Success.TButton", foreground="green")
        
        # Стиль для кнопки остановки
        style.configure("Danger.TButton", foreground="red")
    
    def log_message(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Ограничение количества строк в логе
        lines = self.log_text.get(1.0, tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete(1.0, f"{len(lines) - 1000}.0")
    
    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Логи очищены")
    
    def update_stats_display(self):
        """Обновление отображения статистики"""
        # Обновление времени сессии
        if self.stats['session_start']:
            session_time = datetime.now() - self.stats['session_start']
            hours, remainder = divmod(int(session_time.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.stats_labels['session_time'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Обновление других статистик
        for key, label in self.stats_labels.items():
            if key != 'session_time' and key != 'last_task_time':
                label.config(text=str(self.stats[key]))
            elif key == 'last_task_time' and self.stats[key]:
                last_time = self.stats[key].strftime("%H:%M:%S")
                label.config(text=last_time)
        
        # Планирование следующего обновления
        self.root.after(1000, self.update_stats_display)
    
    def reset_stats(self):
        """Сброс статистики"""
        if messagebox.askyesno("Сброс статистики", "Вы уверены, что хотите сбросить статистику?"):
            self.stats = {
                'tasks_completed': 0,
                'tasks_failed': 0,
                'likes_count': 0,
                'reposts_count': 0,
                'comments_count': 0,
                'session_start': None,
                'last_task_time': None
            }
            self.save_stats()
            self.log_message("Статистика сброшена")
    
    def start_automation(self):
        """Запуск автоматизации"""
        if self.is_running:
            return
        
        try:
            # Проверка наличия необходимых настроек
            if not self.check_config():
                return
            
            self.is_running = True
            self.stats['session_start'] = datetime.now()
            
            # Обновление интерфейса
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Статус: Запускается...")
            self.progress.start()
            
            self.log_message("Запуск автоматизации...")
            
            # Создание и запуск автоматизации в отдельном потоке
            self.automation_thread = threading.Thread(target=self.run_automation_thread)
            self.automation_thread.daemon = True
            self.automation_thread.start()
            
        except Exception as e:
            self.log_message(f"Ошибка запуска: {e}")
            self.stop_automation()
    
    def stop_automation(self):
        """Остановка автоматизации"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.automation:
            self.automation.is_running = False
        
        # Обновление интерфейса
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Статус: Остановлен")
        self.progress.stop()
        
        self.log_message("Автоматизация остановлена")
        self.save_stats()
    
    def check_config(self) -> bool:
        """Проверка конфигурации"""
        required_env_vars = ['API_ID', 'API_HASH', 'PHONE_NUMBER']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            missing_text = '\n'.join(missing_vars)
            messagebox.showerror("Ошибка конфигурации", 
                               f"Отсутствуют переменные окружения:\n{missing_text}\n\n"
                               f"Создайте файл .env с необходимыми настройками.")
            return False
        
        return True
    
    def run_automation_thread(self):
        """Запуск автоматизации в отдельном потоке"""
        try:
            # Создание нового event loop для потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Создание экземпляра автоматизации с настройками из GUI
            self.automation = VKTaskAutomation()
            self.automation.headless = self.headless_var.get()
            self.automation.task_delay = int(self.delay_var.get())
            self.automation.gui_callback = self.on_task_completed
            
            # Обновление статуса
            self.root.after(0, lambda: self.status_label.config(text="Статус: Работает"))
            
            # Запуск автоматизации
            loop.run_until_complete(self.automation.start())
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Ошибка в потоке автоматизации: {e}"))
        finally:
            self.root.after(0, self.stop_automation)
    
    def on_task_completed(self, task_type: str, success: bool):
        """Callback для обновления статистики при выполнении задания"""
        if success:
            self.stats['tasks_completed'] += 1
            self.stats['last_task_time'] = datetime.now()
            
            if task_type == 'like':
                self.stats['likes_count'] += 1
            elif task_type == 'repost':
                self.stats['reposts_count'] += 1
            elif task_type == 'comment':
                self.stats['comments_count'] += 1
                
            self.log_message(f"Задание выполнено: {task_type}")
        else:
            self.stats['tasks_failed'] += 1
            self.log_message(f"Задание не выполнено: {task_type}")
        
        self.save_stats()
    
    def save_stats(self):
        """Сохранение статистики в файл"""
        try:
            stats_to_save = self.stats.copy()
            # Конвертация datetime в строку для JSON
            if stats_to_save['session_start']:
                stats_to_save['session_start'] = stats_to_save['session_start'].isoformat()
            if stats_to_save['last_task_time']:
                stats_to_save['last_task_time'] = stats_to_save['last_task_time'].isoformat()
            
            with open('automation_stats.json', 'w', encoding='utf-8') as f:
                json.dump(stats_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_message(f"Ошибка сохранения статистики: {e}")
    
    def load_stats(self):
        """Загрузка статистики из файла"""
        try:
            if os.path.exists('automation_stats.json'):
                with open('automation_stats.json', 'r', encoding='utf-8') as f:
                    loaded_stats = json.load(f)
                
                # Конвертация строк обратно в datetime
                if loaded_stats.get('session_start'):
                    loaded_stats['session_start'] = datetime.fromisoformat(loaded_stats['session_start'])
                if loaded_stats.get('last_task_time'):
                    loaded_stats['last_task_time'] = datetime.fromisoformat(loaded_stats['last_task_time'])
                
                self.stats.update(loaded_stats)
        except Exception as e:
            print(f"Ошибка загрузки статистики: {e}")
    
    def on_closing(self):
        """Обработка закрытия приложения"""
        if self.is_running:
            if messagebox.askokcancel("Закрытие", "Автоматизация запущена. Остановить и закрыть?"):
                self.stop_automation()
                time.sleep(1)  # Даем время для корректной остановки
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Запуск GUI приложения"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


class GUILogHandler(logging.Handler):
    """Обработчик логов для GUI"""
    
    def __init__(self, gui_app):
        super().__init__()
        self.gui_app = gui_app
    
    def emit(self, record):
        """Отправка лог-сообщения в GUI"""
        try:
            message = self.format(record)
            # Планируем обновление GUI в главном потоке
            self.gui_app.root.after(0, lambda: self.gui_app.log_message(message))
        except Exception:
            pass


def main():
    """Главная функция"""
    app = VKBotGUI()
    app.run()


if __name__ == "__main__":
    main()