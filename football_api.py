import requests
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

class FootballAPI:
    def __init__(self):
        self.api_key = os.getenv('FOOTBALL_API_KEY')
        self.base_url = os.getenv('FOOTBALL_API_BASE_URL', 'https://api.football-data.org/v4')
        self.headers = {
            'X-Auth-Token': self.api_key,
            'Content-Type': 'application/json'
        }
        
    async def get_upcoming_matches(self, days_ahead: int = 1) -> List[Dict]:
        """Получает предстоящие матчи на указанное количество дней вперед"""
        try:
            tomorrow = datetime.now() + timedelta(days=days_ahead)
            date_str = tomorrow.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/matches"
            params = {
                'dateFrom': date_str,
                'dateTo': date_str,
                'status': 'SCHEDULED'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('matches', [])
                    else:
                        print(f"Error fetching matches: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error in get_upcoming_matches: {e}")
            return []
    
    async def get_team_stats(self, team_id: int) -> Dict:
        """Получает статистику команды"""
        try:
            url = f"{self.base_url}/teams/{team_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
                    
        except Exception as e:
            print(f"Error in get_team_stats: {e}")
            return {}
    
    async def get_league_standings(self, competition_id: int) -> Dict:
        """Получает турнирную таблицу"""
        try:
            url = f"{self.base_url}/competitions/{competition_id}/standings"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
                    
        except Exception as e:
            print(f"Error in get_league_standings: {e}")
            return {}
    
    async def get_team_matches(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Получает последние матчи команды"""
        try:
            url = f"{self.base_url}/teams/{team_id}/matches"
            params = {
                'status': 'FINISHED',
                'limit': limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('matches', [])
                    return []
                    
        except Exception as e:
            print(f"Error in get_team_matches: {e}")
            return []
    
    async def get_head_to_head(self, team1_id: int, team2_id: int, limit: int = 5) -> List[Dict]:
        """Получает статистику личных встреч между командами"""
        try:
            # Получаем последние матчи обеих команд и фильтруем их
            team1_matches = await self.get_team_matches(team1_id, 50)
            
            h2h_matches = []
            for match in team1_matches:
                home_team_id = match.get('homeTeam', {}).get('id')
                away_team_id = match.get('awayTeam', {}).get('id')
                
                if (home_team_id == team1_id and away_team_id == team2_id) or \
                   (home_team_id == team2_id and away_team_id == team1_id):
                    h2h_matches.append(match)
                    
                if len(h2h_matches) >= limit:
                    break
                    
            return h2h_matches
            
        except Exception as e:
            print(f"Error in get_head_to_head: {e}")
            return []

class FreeFootballAPI:
    """Альтернативный бесплатный API для получения футбольных данных"""
    
    def __init__(self):
        self.base_url = "https://api.football-data.org/v4"
        # Бесплатный токен с ограничениями
        self.headers = {
            'X-Auth-Token': 'YOUR_FREE_TOKEN_HERE'
        }
    
    async def get_popular_leagues(self) -> List[int]:
        """Возвращает ID популярных лиг"""
        return [
            2021,  # Premier League
            2014,  # La Liga
            2002,  # Bundesliga
            2019,  # Serie A
            2015,  # Ligue 1
            2001,  # Champions League
        ]
    
    async def get_mock_data(self) -> List[Dict]:
        """Возвращает тестовые данные для демонстрации"""
        return [
            {
                "id": 1,
                "homeTeam": {"id": 1, "name": "Manchester United", "shortName": "MUN"},
                "awayTeam": {"id": 2, "name": "Chelsea", "shortName": "CHE"},
                "competition": {"name": "Premier League"},
                "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "SCHEDULED"
            },
            {
                "id": 2,
                "homeTeam": {"id": 3, "name": "Barcelona", "shortName": "BAR"},
                "awayTeam": {"id": 4, "name": "Real Madrid", "shortName": "RMA"},
                "competition": {"name": "La Liga"},
                "utcDate": (datetime.now() + timedelta(days=1)).isoformat(),
                "status": "SCHEDULED"
            }
        ]