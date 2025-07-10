#!/usr/bin/env python3
"""
Demo mode для Football Betting Bot

Демонстрирует функциональность анализатора с тестовыми данными
без необходимости реальных API ключей.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from analyzer import FootballAnalyzer

class MockFootballAPI:
    """Мок API для демонстрации"""
    
    def __init__(self):
        self.mock_matches = [
            {
                "id": 1,
                "homeTeam": {"id": 1, "name": "Манчестер Юнайтед", "shortName": "MUN"},
                "awayTeam": {"id": 2, "name": "Челси", "shortName": "CHE"},
                "competition": {"name": "Премьер-лига"},
                "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "SCHEDULED"
            },
            {
                "id": 2,
                "homeTeam": {"id": 3, "name": "Барселона", "shortName": "BAR"},
                "awayTeam": {"id": 4, "name": "Реал Мадрид", "shortName": "RMA"},
                "competition": {"name": "Ла Лига"},
                "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "SCHEDULED"
            },
            {
                "id": 3,
                "homeTeam": {"id": 5, "name": "Бавария", "shortName": "BAY"},
                "awayTeam": {"id": 6, "name": "Боруссия", "shortName": "BVB"},
                "competition": {"name": "Бундеслига"},
                "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "SCHEDULED"
            }
        ]
        
        self.mock_team_matches = {
            1: [  # Манчестер Юнайтед
                {
                    "homeTeam": {"id": 1}, "awayTeam": {"id": 7},
                    "score": {"fullTime": {"home": 2, "away": 1}}
                },
                {
                    "homeTeam": {"id": 8}, "awayTeam": {"id": 1},
                    "score": {"fullTime": {"home": 0, "away": 3}}
                },
                {
                    "homeTeam": {"id": 1}, "awayTeam": {"id": 9},
                    "score": {"fullTime": {"home": 1, "away": 1}}
                },
                {
                    "homeTeam": {"id": 10}, "awayTeam": {"id": 1},
                    "score": {"fullTime": {"home": 2, "away": 4}}
                },
                {
                    "homeTeam": {"id": 1}, "awayTeam": {"id": 11},
                    "score": {"fullTime": {"home": 3, "away": 0}}
                }
            ],
            2: [  # Челси
                {
                    "homeTeam": {"id": 2}, "awayTeam": {"id": 12},
                    "score": {"fullTime": {"home": 1, "away": 2}}
                },
                {
                    "homeTeam": {"id": 13}, "awayTeam": {"id": 2},
                    "score": {"fullTime": {"home": 1, "away": 1}}
                },
                {
                    "homeTeam": {"id": 2}, "awayTeam": {"id": 14},
                    "score": {"fullTime": {"home": 0, "away": 1}}
                },
                {
                    "homeTeam": {"id": 15}, "awayTeam": {"id": 2},
                    "score": {"fullTime": {"home": 0, "away": 2}}
                },
                {
                    "homeTeam": {"id": 2}, "awayTeam": {"id": 16},
                    "score": {"fullTime": {"home": 2, "away": 0}}
                }
            ],
            3: [  # Барселона
                {
                    "homeTeam": {"id": 3}, "awayTeam": {"id": 17},
                    "score": {"fullTime": {"home": 4, "away": 1}}
                },
                {
                    "homeTeam": {"id": 18}, "awayTeam": {"id": 3},
                    "score": {"fullTime": {"home": 0, "away": 2}}
                },
                {
                    "homeTeam": {"id": 3}, "awayTeam": {"id": 19},
                    "score": {"fullTime": {"home": 3, "away": 1}}
                },
                {
                    "homeTeam": {"id": 20}, "awayTeam": {"id": 3},
                    "score": {"fullTime": {"home": 1, "away": 3}}
                },
                {
                    "homeTeam": {"id": 3}, "awayTeam": {"id": 21},
                    "score": {"fullTime": {"home": 2, "away": 0}}
                }
            ],
            4: [  # Реал Мадрид
                {
                    "homeTeam": {"id": 4}, "awayTeam": {"id": 22},
                    "score": {"fullTime": {"home": 3, "away": 1}}
                },
                {
                    "homeTeam": {"id": 23}, "awayTeam": {"id": 4},
                    "score": {"fullTime": {"home": 0, "away": 2}}
                },
                {
                    "homeTeam": {"id": 4}, "awayTeam": {"id": 24},
                    "score": {"fullTime": {"home": 1, "away": 0}}
                },
                {
                    "homeTeam": {"id": 25}, "awayTeam": {"id": 4},
                    "score": {"fullTime": {"home": 2, "away": 2}}
                },
                {
                    "homeTeam": {"id": 4}, "awayTeam": {"id": 26},
                    "score": {"fullTime": {"home": 4, "away": 0}}
                }
            ]
        }
    
    async def get_upcoming_matches(self, days_ahead: int = 1) -> List[Dict]:
        """Возвращает тестовые матчи"""
        return self.mock_matches
    
    async def get_team_matches(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Возвращает тестовые матчи команды"""
        return self.mock_team_matches.get(team_id, [])
    
    async def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> List[Dict]:
        """Возвращает тестовую статистику личных встреч"""
        # Простая тестовая статистика
        return [
            {
                "homeTeam": {"id": team1_id}, 
                "awayTeam": {"id": team2_id},
                "score": {"fullTime": {"home": 2, "away": 1}}
            },
            {
                "homeTeam": {"id": team2_id}, 
                "awayTeam": {"id": team1_id},
                "score": {"fullTime": {"home": 1, "away": 3}}
            }
        ]

class DemoBettingBot:
    """Демо-версия бота для тестирования"""
    
    def __init__(self):
        self.api = MockFootballAPI()
        self.analyzer = FootballAnalyzer(self.api)
    
    async def run_demo(self):
        """Запускает демонстрацию анализа"""
        print("\n🏆 Football Betting Analysis Bot - Demo Mode")
        print("=" * 60)
        
        # Получаем тестовые матчи
        matches = await self.api.get_upcoming_matches()
        
        for i, match in enumerate(matches, 1):
            print(f"\n📍 Анализ матча {i}/{len(matches)}")
            print("-" * 40)
            
            # Анализируем матч
            try:
                analysis = await self.analyzer.analyze_match(match)
                
                # Выводим результат
                self.print_match_analysis(analysis)
                
                # Пауза между анализами
                if i < len(matches):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Ошибка анализа матча: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Демонстрация завершена!")
        print("\n💡 Для запуска реального бота:")
        print("   1. Получите токен у @BotFather в Telegram")
        print("   2. Создайте файл .env с токеном")
        print("   3. Запустите: python main.py")
    
    def print_match_analysis(self, analysis: Dict):
        """Выводит анализ матча в консоль"""
        match = analysis['match']
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        
        print(f"🏟  {home_team} vs {away_team}")
        print(f"🏆 {match['competition']['name']}")
        
        # Форма команд
        home_form = analysis['home_form']
        away_form = analysis['away_form']
        
        print(f"\n📊 Форма команд:")
        print(f"   🏠 {home_team}: {home_form['form_score']}% ({home_form['wins']}П-{home_form['draws']}Н-{home_form['losses']}П)")
        print(f"   ✈️  {away_team}: {away_form['form_score']}% ({away_form['wins']}П-{away_form['draws']}Н-{away_form['losses']}П)")
        
        # Вероятности
        betting = analysis['betting_analysis']
        print(f"\n🎯 Вероятности:")
        print(f"   🏠 Победа {home_team}: {betting['team1_win_prob']}%")
        print(f"   ✈️  Победа {away_team}: {betting['team2_win_prob']}%")
        print(f"   🤝 Ничья: {betting['draw_prob']}%")
        print(f"   ⚽ Тотал >2.5: {betting['over_2_5_prob']}%")
        print(f"   🎯 Обе забьют: {betting['btts_prob']}%")
        
        # Рекомендации
        print(f"\n💡 Рекомендации:")
        if analysis['recommendations']:
            for rec in analysis['recommendations']:
                print(f"   • {rec}")
        else:
            print("   • Матч сложно прогнозируемый")
        
        print(f"\n⭐ Уверенность в прогнозе: {analysis['confidence_score']}%")

if __name__ == "__main__":
    async def main():
        demo = DemoBettingBot()
        await demo.run_demo()
    
    asyncio.run(main())