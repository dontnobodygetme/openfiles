#!/usr/bin/env python3
"""
Модуль для отслеживания результатов ставок и отправки статистики
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from football_api import FootballAPI

class BetTracker:
    """Класс для отслеживания результатов ставок"""
    
    def __init__(self, data_file: str = "bet_history.json"):
        self.data_file = data_file
        self.api = FootballAPI()
        
    def load_bet_history(self) -> Dict:
        """Загружает историю ставок из файла"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"predictions": [], "statistics": {}}
        except Exception as e:
            print(f"Error loading bet history: {e}")
            return {"predictions": [], "statistics": {}}
    
    def save_bet_history(self, data: Dict):
        """Сохраняет историю ставок в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bet history: {e}")
    
    def save_prediction(self, match_data: Dict, predictions: Dict, odds: Dict = None):
        """Сохраняет прогноз для последующего отслеживания"""
        history = self.load_bet_history()
        
        prediction_record = {
            "match_id": match_data.get('id', f"{match_data['homeTeam']['name']}_{match_data['awayTeam']['name']}_{match_data['utcDate']}"),
            "home_team": match_data['homeTeam']['name'],
            "away_team": match_data['awayTeam']['name'],
            "match_date": match_data['utcDate'],
            "predictions": predictions,
            "odds": odds or {},
            "created_at": datetime.now().isoformat(),
            "result_checked": False,
            "actual_result": None,
            "bet_results": {}
        }
        
        history["predictions"].append(prediction_record)
        self.save_bet_history(history)
    
    async def check_match_result(self, match_record: Dict) -> Optional[Dict]:
        """Проверяет результат матча"""
        try:
            # В реальном приложении здесь был бы запрос к API
            # Для демо используем мок-данные
            
            # Генерируем случайный результат на основе хеша названий команд
            home_hash = hash(match_record['home_team']) % 5
            away_hash = hash(match_record['away_team']) % 5
            
            result = {
                "home_goals": max(0, home_hash),
                "away_goals": max(0, away_hash),
                "total_goals": max(0, home_hash) + max(0, away_hash),
                "winner": "home" if home_hash > away_hash else "away" if away_hash > home_hash else "draw",
                "both_scored": max(0, home_hash) > 0 and max(0, away_hash) > 0
            }
            
            return result
            
        except Exception as e:
            print(f"Error checking match result: {e}")
            return None
    
    def evaluate_predictions(self, predictions: Dict, actual_result: Dict) -> Dict:
        """Оценивает точность прогнозов"""
        results = {}
        
        # Проверяем исход матча
        predicted_winner = "home" if predictions.get('team1_win_prob', 0) > max(predictions.get('team2_win_prob', 0), predictions.get('draw_prob', 0)) else \
                          "away" if predictions.get('team2_win_prob', 0) > max(predictions.get('team1_win_prob', 0), predictions.get('draw_prob', 0)) else "draw"
        
        results['match_outcome'] = {
            'predicted': predicted_winner,
            'actual': actual_result['winner'],
            'correct': predicted_winner == actual_result['winner']
        }
        
        # Проверяем тотал больше 2.5
        total_goals = actual_result['total_goals']
        over_25_predicted = predictions.get('over_2_5_prob', 0) > 50
        over_25_actual = total_goals > 2.5
        
        results['over_2_5'] = {
            'predicted': over_25_predicted,
            'actual': over_25_actual,
            'correct': over_25_predicted == over_25_actual
        }
        
        # Проверяем тотал больше 3.5
        over_35_predicted = predictions.get('over_2_5_prob', 0) > 70  # Если очень уверены в >2.5, то и >3.5 вероятно
        over_35_actual = total_goals > 3.5
        
        results['over_3_5'] = {
            'predicted': over_35_predicted,
            'actual': over_35_actual,
            'correct': over_35_predicted == over_35_actual
        }
        
        # Проверяем обе забьют
        btts_predicted = predictions.get('btts_prob', 0) > 50
        btts_actual = actual_result['both_scored']
        
        results['both_teams_score'] = {
            'predicted': btts_predicted,
            'actual': btts_actual,
            'correct': btts_predicted == btts_actual
        }
        
        return results
    
    async def check_pending_results(self) -> List[Dict]:
        """Проверяет результаты всех неподтвержденных прогнозов"""
        history = self.load_bet_history()
        updated_predictions = []
        
        for prediction in history["predictions"]:
            if not prediction.get("result_checked", False):
                # Проверяем, прошло ли достаточно времени после матча
                match_date = datetime.fromisoformat(prediction["match_date"].replace('Z', '+00:00'))
                if datetime.now() > match_date + timedelta(hours=3):
                    
                    actual_result = await self.check_match_result(prediction)
                    if actual_result:
                        bet_results = self.evaluate_predictions(prediction["predictions"], actual_result)
                        
                        prediction["actual_result"] = actual_result
                        prediction["bet_results"] = bet_results
                        prediction["result_checked"] = True
                        prediction["checked_at"] = datetime.now().isoformat()
                        
                        updated_predictions.append(prediction)
        
        if updated_predictions:
            self.save_bet_history(history)
            
        return updated_predictions
    
    def generate_daily_statistics(self, date: datetime = None) -> Dict:
        """Генерирует ежедневную статистику"""
        if date is None:
            date = datetime.now() - timedelta(days=1)  # Вчерашняя дата
        
        history = self.load_bet_history()
        
        # Фильтруем прогнозы за указанную дату
        date_str = date.strftime('%Y-%m-%d')
        daily_predictions = [
            p for p in history["predictions"] 
            if p.get("result_checked", False) and 
            p.get("checked_at", "").startswith(date_str)
        ]
        
        if not daily_predictions:
            return {
                "date": date_str,
                "total_predictions": 0,
                "message": "Нет результатов за этот день"
            }
        
        # Подсчитываем статистику
        stats = {
            "date": date_str,
            "total_predictions": len(daily_predictions),
            "correct_outcomes": 0,
            "correct_over_25": 0,
            "correct_over_35": 0,
            "correct_btts": 0,
            "matches": []
        }
        
        for prediction in daily_predictions:
            bet_results = prediction.get("bet_results", {})
            
            # Подсчитываем правильные прогнозы
            if bet_results.get("match_outcome", {}).get("correct", False):
                stats["correct_outcomes"] += 1
            
            if bet_results.get("over_2_5", {}).get("correct", False):
                stats["correct_over_25"] += 1
                
            if bet_results.get("over_3_5", {}).get("correct", False):
                stats["correct_over_35"] += 1
            
            if bet_results.get("both_teams_score", {}).get("correct", False):
                stats["correct_btts"] += 1
            
            # Добавляем информацию о матче
            match_info = {
                "home_team": prediction["home_team"],
                "away_team": prediction["away_team"],
                "score": f"{prediction['actual_result']['home_goals']}-{prediction['actual_result']['away_goals']}",
                "predictions": bet_results
            }
            stats["matches"].append(match_info)
        
        # Вычисляем проценты успешности
        total = stats["total_predictions"]
        stats["success_rates"] = {
            "match_outcome": round((stats["correct_outcomes"] / total) * 100, 1) if total > 0 else 0,
            "over_2_5": round((stats["correct_over_25"] / total) * 100, 1) if total > 0 else 0,
            "over_3_5": round((stats["correct_over_35"] / total) * 100, 1) if total > 0 else 0,
            "both_teams_score": round((stats["correct_btts"] / total) * 100, 1) if total > 0 else 0
        }
        
        return stats
    
    def format_daily_report(self, stats: Dict) -> str:
        """Форматирует ежедневный отчет для отправки"""
        if stats.get("total_predictions", 0) == 0:
            return f"📊 *Статистика за {stats['date']}*\n\n❌ Прогнозов не было"
        
        text = f"📊 *Статистика ставок за {stats['date']}*\n\n"
        text += f"🎯 Всего прогнозов: {stats['total_predictions']}\n\n"
        
        text += "📈 *Точность прогнозов:*\n"
        text += f"⚽ Исходы матчей: {stats['success_rates']['match_outcome']}% ({stats['correct_outcomes']}/{stats['total_predictions']})\n"
        text += f"📊 Тотал >2.5: {stats['success_rates']['over_2_5']}% ({stats['correct_over_25']}/{stats['total_predictions']})\n"
        text += f"📈 Тотал >3.5: {stats['success_rates']['over_3_5']}% ({stats['correct_over_35']}/{stats['total_predictions']})\n"
        text += f"🎯 Обе забьют: {stats['success_rates']['both_teams_score']}% ({stats['correct_btts']}/{stats['total_predictions']})\n\n"
        
        text += "🏆 *Результаты матчей:*\n"
        for match in stats['matches']:
            text += f"• {match['home_team']} - {match['away_team']} ({match['score']})\n"
            
            # Показываем результаты прогнозов
            results = match['predictions']
            outcome_result = "✅" if results.get('match_outcome', {}).get('correct') else "❌"
            over25_result = "✅" if results.get('over_2_5', {}).get('correct') else "❌"
            btts_result = "✅" if results.get('both_teams_score', {}).get('correct') else "❌"
            
            text += f"  Исход: {outcome_result} | >2.5: {over25_result} | Обе забьют: {btts_result}\n"
        
        return text
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Очищает старые данные"""
        history = self.load_bet_history()
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        history["predictions"] = [
            p for p in history["predictions"]
            if datetime.fromisoformat(p.get("created_at", datetime.now().isoformat())) > cutoff_date
        ]
        
        self.save_bet_history(history)