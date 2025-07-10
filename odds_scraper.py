#!/usr/bin/env python3
"""
Упрощенный модуль для получения коэффициентов от букмекеров
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

class OddsScraper:
    """Класс для получения коэффициентов от букмекеров"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_mock_odds(self, home_team: str, away_team: str) -> Dict:
        """Генерирует тестовые коэффициенты для демонстрации"""
        
        # Генерируем коэффициенты на основе хешей названий команд для консистентности
        home_hash = abs(hash(home_team)) % 100
        away_hash = abs(hash(away_team)) % 100
        
        # Базовые коэффициенты
        home_odds = round(1.5 + (home_hash % 30) / 100, 2)
        away_odds = round(1.8 + (away_hash % 40) / 100, 2)
        draw_odds = round(3.0 + ((home_hash + away_hash) % 50) / 100, 2)
        
        return {
            'fonbet': {
                'match': f"{home_team} vs {away_team}",
                'outcomes': {
                    'home_win': home_odds,
                    'draw': draw_odds,
                    'away_win': away_odds
                },
                'totals': {
                    'over_0_5': round(1.05 + (home_hash % 10) / 100, 2),
                    'under_0_5': round(8.0 + (home_hash % 20) / 10, 2),
                    'over_1_5': round(1.25 + (home_hash % 20) / 100, 2),
                    'under_1_5': round(3.5 + (home_hash % 15) / 10, 2),
                    'over_2_5': round(1.7 + (home_hash % 40) / 100, 2),
                    'under_2_5': round(2.1 + (away_hash % 30) / 100, 2),
                    'over_3_5': round(2.8 + (home_hash % 60) / 100, 2),
                    'under_3_5': round(1.4 + (away_hash % 20) / 100, 2),
                    'over_4_5': round(5.0 + (home_hash % 100) / 100, 2),
                    'under_4_5': round(1.15 + (away_hash % 10) / 100, 2)
                },
                'both_teams_score': {
                    'yes': round(1.85 + ((home_hash + away_hash) % 30) / 100, 2),
                    'no': round(1.95 + (away_hash % 25) / 100, 2)
                },
                'timestamp': datetime.now().isoformat(),
                'bookmaker': 'Fonbet'
            }
        }
    
    def get_best_odds_for_bet(self, odds_data: Dict, bet_type: str) -> Optional[Dict]:
        """Находит лучшие коэффициенты для определенного типа ставки"""
        try:
            fonbet_odds = odds_data.get('fonbet', {})
            
            if bet_type == 'home_win':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('outcomes', {}).get('home_win', 0),
                    'bet_type': 'Победа дома'
                }
            elif bet_type == 'away_win':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('outcomes', {}).get('away_win', 0),
                    'bet_type': 'Победа гостей'
                }
            elif bet_type == 'draw':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('outcomes', {}).get('draw', 0),
                    'bet_type': 'Ничья'
                }
            elif bet_type == 'over_2_5':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('totals', {}).get('over_2_5', 0),
                    'bet_type': 'Тотал больше 2.5'
                }
            elif bet_type == 'under_2_5':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('totals', {}).get('under_2_5', 0),
                    'bet_type': 'Тотал меньше 2.5'
                }
            elif bet_type == 'over_3_5':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('totals', {}).get('over_3_5', 0),
                    'bet_type': 'Тотал больше 3.5'
                }
            elif bet_type == 'under_3_5':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('totals', {}).get('under_3_5', 0),
                    'bet_type': 'Тотал меньше 3.5'
                }
            elif bet_type == 'btts_yes':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('both_teams_score', {}).get('yes', 0),
                    'bet_type': 'Обе команды забьют'
                }
            elif bet_type == 'btts_no':
                return {
                    'bookmaker': 'Fonbet',
                    'odds': fonbet_odds.get('both_teams_score', {}).get('no', 0),
                    'bet_type': 'Обе команды НЕ забьют'
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting best odds: {e}")
            return None
    
    def generate_betting_recommendations(self, odds_data: Dict, predictions: Dict) -> List[str]:
        """Генерирует рекомендации по ставкам с коэффициентами"""
        recommendations = []
        
        try:
            # Рекомендации по исходу матча
            if predictions.get('team1_win_prob', 0) > 60:
                home_odds = self.get_best_odds_for_bet(odds_data, 'home_win')
                if home_odds and home_odds.get('odds', 0) > 1.4:
                    recommendations.append(
                        f"🏠 {home_odds['bet_type']}: {home_odds['odds']} ({home_odds['bookmaker']})"
                    )
            
            if predictions.get('team2_win_prob', 0) > 60:
                away_odds = self.get_best_odds_for_bet(odds_data, 'away_win')
                if away_odds and away_odds.get('odds', 0) > 1.4:
                    recommendations.append(
                        f"✈️ {away_odds['bet_type']}: {away_odds['odds']} ({away_odds['bookmaker']})"
                    )
            
            if predictions.get('draw_prob', 0) > 35:
                draw_odds = self.get_best_odds_for_bet(odds_data, 'draw')
                if draw_odds and draw_odds.get('odds', 0) > 2.5:
                    recommendations.append(
                        f"🤝 {draw_odds['bet_type']}: {draw_odds['odds']} ({draw_odds['bookmaker']})"
                    )
            
            # Рекомендации по тоталам
            if predictions.get('over_2_5_prob', 0) > 70:
                over_25_odds = self.get_best_odds_for_bet(odds_data, 'over_2_5')
                if over_25_odds and over_25_odds.get('odds', 0) > 1.3:
                    recommendations.append(
                        f"📈 {over_25_odds['bet_type']}: {over_25_odds['odds']} ({over_25_odds['bookmaker']})"
                    )
            
            if predictions.get('over_2_5_prob', 0) < 30:
                under_25_odds = self.get_best_odds_for_bet(odds_data, 'under_2_5')
                if under_25_odds and under_25_odds.get('odds', 0) > 1.3:
                    recommendations.append(
                        f"📉 {under_25_odds['bet_type']}: {under_25_odds['odds']} ({under_25_odds['bookmaker']})"
                    )
            
            # Дополнительные тоталы
            if predictions.get('total_goals_prediction', 0) > 3.5:
                over_35_odds = self.get_best_odds_for_bet(odds_data, 'over_3_5')
                if over_35_odds and over_35_odds.get('odds', 0) > 2.0:
                    recommendations.append(
                        f"📊 {over_35_odds['bet_type']}: {over_35_odds['odds']} ({over_35_odds['bookmaker']})"
                    )
            
            # Рекомендации по обеим забьют
            if predictions.get('btts_prob', 0) > 65:
                btts_yes_odds = self.get_best_odds_for_bet(odds_data, 'btts_yes')
                if btts_yes_odds and btts_yes_odds.get('odds', 0) > 1.5:
                    recommendations.append(
                        f"🎯 {btts_yes_odds['bet_type']}: {btts_yes_odds['odds']} ({btts_yes_odds['bookmaker']})"
                    )
            
            if predictions.get('btts_prob', 0) < 35:
                btts_no_odds = self.get_best_odds_for_bet(odds_data, 'btts_no')
                if btts_no_odds and btts_no_odds.get('odds', 0) > 1.5:
                    recommendations.append(
                        f"❌ {btts_no_odds['bet_type']}: {btts_no_odds['odds']} ({btts_no_odds['bookmaker']})"
                    )
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def format_odds_display(self, odds_data: Dict) -> str:
        """Форматирует коэффициенты для отображения"""
        if not odds_data:
            return ""
        
        fonbet = odds_data.get('fonbet', {})
        if not fonbet:
            return ""
        
        text = "\n💰 *Коэффициенты Fonbet:*\n"
        
        # Исходы
        outcomes = fonbet.get('outcomes', {})
        text += f"🏠 П1: {outcomes.get('home_win', 'N/A')} | "
        text += f"🤝 X: {outcomes.get('draw', 'N/A')} | "
        text += f"✈️ П2: {outcomes.get('away_win', 'N/A')}\n"
        
        # Тоталы
        totals = fonbet.get('totals', {})
        text += f"📈 >2.5: {totals.get('over_2_5', 'N/A')} | "
        text += f"📉 <2.5: {totals.get('under_2_5', 'N/A')}\n"
        text += f"📊 >3.5: {totals.get('over_3_5', 'N/A')} | "
        text += f"📊 <3.5: {totals.get('under_3_5', 'N/A')}\n"
        
        # Обе забьют
        btts = fonbet.get('both_teams_score', {})
        text += f"🎯 Обе забьют: Да {btts.get('yes', 'N/A')} | Нет {btts.get('no', 'N/A')}\n"
        
        return text