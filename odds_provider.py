#!/usr/bin/env python3
"""
Модуль для получения коэффициентов от букмекерских контор
Поддерживает Фонбет и другие популярные букмекеры
"""

import requests
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

class OddsProvider:
    """Класс для получения коэффициентов от букмекерских контор"""
    
    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    async def get_fonbet_odds(self, home_team: str, away_team: str) -> Dict:
        """Получает коэффициенты с Фонбета"""
        try:
            # Тестовые данные для демонстрации
            # В реальном проекте здесь был бы парсинг сайта Фонбета
            mock_odds = {
                'bookmaker': 'Fonbet',
                'match': f"{home_team} vs {away_team}",
                'home_win': round(1.5 + (hash(home_team) % 100) / 100, 2),
                'draw': round(3.0 + (hash(home_team + away_team) % 100) / 100, 2),
                'away_win': round(2.0 + (hash(away_team) % 100) / 100, 2),
                'totals': {
                    'over_0_5': round(1.1 + (hash(home_team) % 20) / 100, 2),
                    'under_0_5': round(5.0 + (hash(home_team) % 50) / 100, 2),
                    'over_1_5': round(1.2 + (hash(home_team) % 30) / 100, 2),
                    'under_1_5': round(3.5 + (hash(home_team) % 40) / 100, 2),
                    'over_2_5': round(1.6 + (hash(home_team) % 60) / 100, 2),
                    'under_2_5': round(2.3 + (hash(home_team) % 30) / 100, 2),
                    'over_3_5': round(2.5 + (hash(home_team) % 80) / 100, 2),
                    'under_3_5': round(1.5 + (hash(home_team) % 20) / 100, 2),
                    'over_4_5': round(4.0 + (hash(home_team) % 100) / 100, 2),
                    'under_4_5': round(1.2 + (hash(home_team) % 15) / 100, 2),
                },
                'both_teams_score': {
                    'yes': round(1.8 + (hash(home_team + away_team) % 40) / 100, 2),
                    'no': round(2.0 + (hash(away_team) % 30) / 100, 2)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return mock_odds
            
        except Exception as e:
            print(f"Error fetching Fonbet odds: {e}")
            return {}
    
    async def get_betcity_odds(self, home_team: str, away_team: str) -> Dict:
        """Получает коэффициенты с BetCity"""
        try:
            # Тестовые данные
            mock_odds = {
                'bookmaker': 'BetCity',
                'match': f"{home_team} vs {away_team}",
                'home_win': round(1.6 + (hash(home_team) % 90) / 100, 2),
                'draw': round(3.1 + (hash(home_team + away_team) % 80) / 100, 2),
                'away_win': round(2.1 + (hash(away_team) % 90) / 100, 2),
                'totals': {
                    'over_2_5': round(1.7 + (hash(home_team) % 50) / 100, 2),
                    'under_2_5': round(2.2 + (hash(home_team) % 40) / 100, 2),
                    'over_3_5': round(2.6 + (hash(home_team) % 70) / 100, 2),
                    'under_3_5': round(1.4 + (hash(home_team) % 25) / 100, 2),
                },
                'both_teams_score': {
                    'yes': round(1.9 + (hash(home_team + away_team) % 30) / 100, 2),
                    'no': round(1.9 + (hash(away_team) % 35) / 100, 2)
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return mock_odds
            
        except Exception as e:
            print(f"Error fetching BetCity odds: {e}")
            return {}
    
    async def get_all_odds(self, home_team: str, away_team: str) -> List[Dict]:
        """Получает коэффициенты от всех букмекеров"""
        try:
            # Получаем коэффициенты параллельно
            odds_tasks = [
                self.get_fonbet_odds(home_team, away_team),
                self.get_betcity_odds(home_team, away_team)
            ]
            
            all_odds = await asyncio.gather(*odds_tasks)
            
            # Фильтруем пустые результаты
            return [odds for odds in all_odds if odds]
            
        except Exception as e:
            print(f"Error fetching all odds: {e}")
            return []
    
    def find_best_odds(self, all_odds: List[Dict], bet_type: str) -> Optional[Dict]:
        """Находит лучшие коэффициенты для определенного типа ставки"""
        if not all_odds:
            return None
            
        best_odds = None
        best_value = 0
        
        for odds in all_odds:
            try:
                if bet_type == 'home_win':
                    value = odds.get('home_win', 0)
                elif bet_type == 'draw':
                    value = odds.get('draw', 0)
                elif bet_type == 'away_win':
                    value = odds.get('away_win', 0)
                elif bet_type == 'over_2_5':
                    value = odds.get('totals', {}).get('over_2_5', 0)
                elif bet_type == 'under_2_5':
                    value = odds.get('totals', {}).get('under_2_5', 0)
                elif bet_type == 'over_3_5':
                    value = odds.get('totals', {}).get('over_3_5', 0)
                elif bet_type == 'under_3_5':
                    value = odds.get('totals', {}).get('under_3_5', 0)
                elif bet_type == 'btts_yes':
                    value = odds.get('both_teams_score', {}).get('yes', 0)
                elif bet_type == 'btts_no':
                    value = odds.get('both_teams_score', {}).get('no', 0)
                else:
                    continue
                    
                if value > best_value:
                    best_value = value
                    best_odds = {
                        'bookmaker': odds.get('bookmaker', 'Unknown'),
                        'odds': value,
                        'bet_type': bet_type
                    }
                    
            except Exception as e:
                continue
                
        return best_odds
    
    def compare_odds(self, all_odds: List[Dict]) -> Dict:
        """Сравнивает коэффициенты разных букмекеров"""
        if not all_odds:
            return {}
            
        comparison = {
            'best_odds': {},
            'all_bookmakers': all_odds,
            'comparison_time': datetime.now().isoformat()
        }
        
        # Типы ставок для сравнения
        bet_types = [
            'home_win', 'draw', 'away_win',
            'over_2_5', 'under_2_5', 'over_3_5', 'under_3_5',
            'btts_yes', 'btts_no'
        ]
        
        for bet_type in bet_types:
            best = self.find_best_odds(all_odds, bet_type)
            if best:
                comparison['best_odds'][bet_type] = best
                
        return comparison
    
    def get_odds_recommendations(self, comparison: Dict, our_predictions: Dict) -> List[str]:
        """Генерирует рекомендации на основе сравнения коэффициентов и наших прогнозов"""
        recommendations = []
        
        if not comparison.get('best_odds'):
            return recommendations
            
        best_odds = comparison['best_odds']
        
        # Рекомендации по исходу матча
        if our_predictions.get('team1_win_prob', 0) > 60:
            home_odds = best_odds.get('home_win', {})
            if home_odds.get('odds', 0) > 1.5:
                recommendations.append(
                    f"🎯 Победа дома: {home_odds.get('odds')} у {home_odds.get('bookmaker')}"
                )
        
        if our_predictions.get('team2_win_prob', 0) > 60:
            away_odds = best_odds.get('away_win', {})
            if away_odds.get('odds', 0) > 1.5:
                recommendations.append(
                    f"🎯 Победа гостей: {away_odds.get('odds')} у {away_odds.get('bookmaker')}"
                )
        
        # Рекомендации по тоталам
        if our_predictions.get('over_2_5_prob', 0) > 70:
            over_25_odds = best_odds.get('over_2_5', {})
            if over_25_odds.get('odds', 0) > 1.4:
                recommendations.append(
                    f"📈 Тотал >2.5: {over_25_odds.get('odds')} у {over_25_odds.get('bookmaker')}"
                )
        
        if our_predictions.get('over_2_5_prob', 0) < 30:
            under_25_odds = best_odds.get('under_2_5', {})
            if under_25_odds.get('odds', 0) > 1.4:
                recommendations.append(
                    f"📉 Тотал <2.5: {under_25_odds.get('odds')} у {under_25_odds.get('bookmaker')}"
                )
        
        # Рекомендации по обеим забьют
        if our_predictions.get('btts_prob', 0) > 65:
            btts_yes_odds = best_odds.get('btts_yes', {})
            if btts_yes_odds.get('odds', 0) > 1.5:
                recommendations.append(
                    f"🎯 Обе забьют: {btts_yes_odds.get('odds')} у {btts_yes_odds.get('bookmaker')}"
                )
        
        if our_predictions.get('btts_prob', 0) < 35:
            btts_no_odds = best_odds.get('btts_no', {})
            if btts_no_odds.get('odds', 0) > 1.5:
                recommendations.append(
                    f"❌ Обе НЕ забьют: {btts_no_odds.get('odds')} у {btts_no_odds.get('bookmaker')}"
                )
        
        return recommendations
    
    async def close(self):
        """Закрывает сессию"""
        if self.session:
            await self.session.close()

class OddsAnalyzer:
    """Анализатор коэффициентов для поиска ценных ставок"""
    
    def __init__(self):
        self.odds_provider = OddsProvider()
    
    def calculate_implied_probability(self, odds: float) -> float:
        """Вычисляет подразумеваемую вероятность из коэффициента"""
        if odds <= 0:
            return 0
        return (1 / odds) * 100
    
    def find_value_bets(self, our_predictions: Dict, market_odds: Dict) -> List[Dict]:
        """Находит ценные ставки (когда наш прогноз превышает рыночную вероятность)"""
        value_bets = []
        
        predictions_mapping = {
            'team1_win_prob': 'home_win',
            'team2_win_prob': 'away_win',
            'draw_prob': 'draw',
            'over_2_5_prob': 'over_2_5',
            'btts_prob': 'btts_yes'
        }
        
        for pred_key, odds_key in predictions_mapping.items():
            our_prob = our_predictions.get(pred_key, 0)
            
            if odds_key in market_odds:
                market_odds_value = market_odds[odds_key].get('odds', 0)
                implied_prob = self.calculate_implied_probability(market_odds_value)
                
                # Если наша вероятность выше рыночной на 10%+, это ценная ставка
                if our_prob > implied_prob + 10:
                    value_bets.append({
                        'bet_type': odds_key,
                        'our_probability': our_prob,
                        'market_probability': implied_prob,
                        'odds': market_odds_value,
                        'bookmaker': market_odds[odds_key].get('bookmaker'),
                        'value': our_prob - implied_prob
                    })
        
        return sorted(value_bets, key=lambda x: x['value'], reverse=True)
    
    async def get_enhanced_recommendations(self, home_team: str, away_team: str, 
                                         our_predictions: Dict) -> Dict:
        """Получает расширенные рекомендации с учетом коэффициентов"""
        try:
            # Получаем коэффициенты
            all_odds = await self.odds_provider.get_all_odds(home_team, away_team)
            
            if not all_odds:
                return {
                    'odds_available': False,
                    'recommendations': [],
                    'value_bets': []
                }
            
            # Сравниваем коэффициенты
            comparison = self.odds_provider.compare_odds(all_odds)
            
            # Получаем рекомендации
            recommendations = self.odds_provider.get_odds_recommendations(
                comparison, our_predictions
            )
            
            # Находим ценные ставки
            value_bets = self.find_value_bets(our_predictions, comparison.get('best_odds', {}))
            
            return {
                'odds_available': True,
                'all_odds': all_odds,
                'best_odds': comparison.get('best_odds', {}),
                'recommendations': recommendations,
                'value_bets': value_bets,
                'comparison_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in get_enhanced_recommendations: {e}")
            return {
                'odds_available': False,
                'error': str(e),
                'recommendations': [],
                'value_bets': []
            }
    
    async def close(self):
        """Закрывает провайдер коэффициентов"""
        await self.odds_provider.close()