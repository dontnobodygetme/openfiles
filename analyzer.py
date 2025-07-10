from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import statistics
from football_api import FootballAPI

class FootballAnalyzer:
    def __init__(self, api: FootballAPI):
        self.api = api
        
    def calculate_team_form(self, matches: List[Dict], team_id: int) -> Dict:
        """Вычисляет форму команды на основе последних матчей"""
        if not matches:
            return {"form_score": 50, "wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
        
        wins = draws = losses = goals_for = goals_against = 0
        
        for match in matches[-5:]:  # Последние 5 матчей
            home_team = match.get('homeTeam', {})
            away_team = match.get('awayTeam', {})
            score = match.get('score', {}).get('fullTime', {})
            
            home_goals = score.get('home', 0) or 0
            away_goals = score.get('away', 0) or 0
            
            is_home = home_team.get('id') == team_id
            
            if is_home:
                goals_for += home_goals
                goals_against += away_goals
                if home_goals > away_goals:
                    wins += 1
                elif home_goals == away_goals:
                    draws += 1
                else:
                    losses += 1
            else:
                goals_for += away_goals
                goals_against += home_goals
                if away_goals > home_goals:
                    wins += 1
                elif away_goals == home_goals:
                    draws += 1
                else:
                    losses += 1
        
        total_matches = wins + draws + losses
        if total_matches == 0:
            form_score = 50
        else:
            form_score = (wins * 3 + draws) / (total_matches * 3) * 100
        
        return {
            "form_score": round(form_score, 1),
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against
        }
    
    def analyze_head_to_head(self, h2h_matches: List[Dict], team1_id: int, team2_id: int) -> Dict:
        """Анализирует статистику личных встреч"""
        if not h2h_matches:
            return {"advantage": "neutral", "team1_wins": 0, "team2_wins": 0, "draws": 0}
        
        team1_wins = team2_wins = draws = 0
        
        for match in h2h_matches:
            home_team = match.get('homeTeam', {})
            away_team = match.get('awayTeam', {})
            score = match.get('score', {}).get('fullTime', {})
            
            home_goals = score.get('home', 0) or 0
            away_goals = score.get('away', 0) or 0
            
            if home_goals > away_goals:
                if home_team.get('id') == team1_id:
                    team1_wins += 1
                else:
                    team2_wins += 1
            elif home_goals < away_goals:
                if away_team.get('id') == team1_id:
                    team1_wins += 1
                else:
                    team2_wins += 1
            else:
                draws += 1
        
        total = team1_wins + team2_wins + draws
        if total == 0:
            advantage = "neutral"
        elif team1_wins > team2_wins:
            advantage = "team1"
        elif team2_wins > team1_wins:
            advantage = "team2"
        else:
            advantage = "neutral"
        
        return {
            "advantage": advantage,
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws,
            "total_matches": total
        }
    
    def calculate_betting_odds(self, team1_form: Dict, team2_form: Dict, h2h: Dict, is_home: bool = True) -> Dict:
        """Вычисляет рекомендуемые ставки на основе анализа"""
        
        # Базовые вероятности
        team1_strength = team1_form['form_score']
        team2_strength = team2_form['form_score']
        
        # Учитываем домашнее преимущество
        if is_home:
            team1_strength += 5  # Домашнее преимущество
        
        # Учитываем личные встречи
        if h2h['advantage'] == 'team1':
            team1_strength += 3
        elif h2h['advantage'] == 'team2':
            team2_strength += 3
        
        # Нормализуем вероятности
        total_strength = team1_strength + team2_strength
        team1_prob = team1_strength / total_strength
        team2_prob = team2_strength / total_strength
        draw_prob = 0.25  # Базовая вероятность ничьи
        
        # Нормализуем все вероятности
        total_prob = team1_prob + team2_prob + draw_prob
        team1_prob /= total_prob
        team2_prob /= total_prob
        draw_prob /= total_prob
        
        # Анализируем голы
        team1_goals_avg = team1_form['goals_for'] / 5 if team1_form['goals_for'] else 1
        team2_goals_avg = team2_form['goals_for'] / 5 if team2_form['goals_for'] else 1
        total_goals_avg = team1_goals_avg + team2_goals_avg
        
        return {
            "team1_win_prob": round(team1_prob * 100, 1),
            "team2_win_prob": round(team2_prob * 100, 1),
            "draw_prob": round(draw_prob * 100, 1),
            "over_2_5_prob": round(min(85, max(15, total_goals_avg * 30)), 1),
            "btts_prob": round(min(80, max(20, (team1_goals_avg + team2_goals_avg) * 25)), 1),
            "total_goals_prediction": round(total_goals_avg, 1)
        }
    
    def generate_recommendations(self, match: Dict, analysis: Dict) -> List[str]:
        """Генерирует текстовые рекомендации по ставкам"""
        recommendations = []
        
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        
        # Рекомендации по исходу матча
        if analysis['team1_win_prob'] > 60:
            recommendations.append(f"🏠 Победа {home_team} (вероятность {analysis['team1_win_prob']}%)")
        elif analysis['team2_win_prob'] > 60:
            recommendations.append(f"✈️ Победа {away_team} (вероятность {analysis['team2_win_prob']}%)")
        elif analysis['draw_prob'] > 35:
            recommendations.append(f"🤝 Ничья (вероятность {analysis['draw_prob']}%)")
        
        # Рекомендации по голам
        if analysis['over_2_5_prob'] > 70:
            recommendations.append(f"⚽️ Тотал больше 2.5 голов (вероятность {analysis['over_2_5_prob']}%)")
        elif analysis['over_2_5_prob'] < 30:
            recommendations.append(f"🚫 Тотал меньше 2.5 голов (вероятность {100-analysis['over_2_5_prob']}%)")
        
        # Рекомендации по обеим забьют
        if analysis['btts_prob'] > 65:
            recommendations.append(f"🎯 Обе команды забьют (вероятность {analysis['btts_prob']}%)")
        elif analysis['btts_prob'] < 35:
            recommendations.append(f"❌ Обе команды НЕ забьют (вероятность {100-analysis['btts_prob']}%)")
        
        return recommendations
    
    async def analyze_match(self, match: Dict) -> Dict:
        """Полный анализ матча"""
        home_team_id = match['homeTeam']['id']
        away_team_id = match['awayTeam']['id']
        
        # Получаем данные для анализа
        home_matches = await self.api.get_team_matches(home_team_id, 10)
        away_matches = await self.api.get_team_matches(away_team_id, 10)
        h2h_matches = await self.api.get_head_to_head(home_team_id, away_team_id, 5)
        
        # Анализируем форму команд
        home_form = self.calculate_team_form(home_matches, home_team_id)
        away_form = self.calculate_team_form(away_matches, away_team_id)
        
        # Анализируем личные встречи
        h2h_analysis = self.analyze_head_to_head(h2h_matches, home_team_id, away_team_id)
        
        # Вычисляем вероятности и рекомендации
        betting_analysis = self.calculate_betting_odds(home_form, away_form, h2h_analysis, True)
        
        # Генерируем рекомендации
        recommendations = self.generate_recommendations(match, betting_analysis)
        
        return {
            "match": match,
            "home_form": home_form,
            "away_form": away_form,
            "head_to_head": h2h_analysis,
            "betting_analysis": betting_analysis,
            "recommendations": recommendations,
            "confidence_score": self._calculate_confidence(home_form, away_form, h2h_analysis)
        }
    
    def _calculate_confidence(self, home_form: Dict, away_form: Dict, h2h: Dict) -> int:
        """Вычисляет уровень уверенности в прогнозе"""
        confidence = 50
        
        # Увеличиваем уверенность если есть четкий фаворит по форме
        form_diff = abs(home_form['form_score'] - away_form['form_score'])
        confidence += min(30, form_diff)
        
        # Увеличиваем уверенность если есть статистика личных встреч
        if h2h['total_matches'] >= 3:
            confidence += 10
        
        # Увеличиваем уверенность если у команд стабильная статистика
        home_matches = home_form['wins'] + home_form['draws'] + home_form['losses']
        away_matches = away_form['wins'] + away_form['draws'] + away_form['losses']
        
        if home_matches >= 5 and away_matches >= 5:
            confidence += 10
        
        return min(95, confidence)