import os
import requests
from datetime import datetime, timedelta

API_KEY = "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba"
BASE_URL = "https://api-baseball.p.rapidapi.com/games"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-baseball.p.rapidapi.com"
}

def get_todays_mlb_games():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "league": "1", "season": "2024"}  # Liga 1 = MLB
    response = requests.get(BASE_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        print("❌ Error MLB:", response.text)
        return []
def analyze_mlb_game_v2(game):
    home = game["teams"]["home"]["name"]
    away = game["teams"]["away"]["name"]

    try:
        stats = game.get("teams", {})
        runs_home = float(game["scores"]["home"]["total"])
        runs_away = float(game["scores"]["away"]["total"])
    except:
        return None

    # Análisis simplificado de lógica ofensiva
    total_runs = runs_home + runs_away
    pick = None
    reason = ""

    if total_runs >= 9:
        pick = "Over 8.5 carreras"
        reason = f"{home} y {away} promedian {total_runs:.1f} carreras por partido combinadas. Potencial ofensivo alto."
    elif total_runs <= 6:
        pick = "Under 7.5 carreras"
        reason = f"{home} y {away} han tenido bajos totales recientemente. Promedio combinado: {total_runs:.1f}."

    if not pick:
        if runs_home > runs_away:
            pick = f"Gana {home}"
            reason = f"{home} ha anotado más que {away} recientemente. Ventaja ofensiva."
        else:
            pick = f"Gana {away}"
            reason = f"{away} muestra mejor forma ofensiva que {home}."

    return {
        "match": f"{home} vs {away}",
        "pick": pick,
        "confidence": "Alta",
        "reason": reason
    }