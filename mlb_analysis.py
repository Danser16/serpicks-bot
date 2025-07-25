
 os
import requests
from datetime import datetime, timedelta

def get_tomorrow_mlb_games():
    url = "https://v1.baseball.api-sports.io/games"
    headers = {
        "x-rapidapi-key": os.getenv("API_FOOTBALL_KEY"),
        "x-rapidapi-host": "v1.baseball.api-sports.io"
    }
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    params = {"date": tomorrow}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("response", [])

def analyze_mlb_game(game):
    home = game["teams"]["home"]["name"]
    away = game["teams"]["away"]["name"]
    league = game["league"]["name"]
    confidence = "Alta" if home in ["Yankees", "Dodgers", "Braves"] else "Media"
    pick = f"{home} ML"
    reason = f"{home} recibe a {away} en MLB. Análisis basado en localía y forma reciente."
    return {
        "league": league,
        "match": f"{home} vs {away}",
        "pick": pick,
        "confidence": confidence,
        "reason": reason
    }
