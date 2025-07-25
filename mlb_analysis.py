import os
import requests
from datetime import datetime, timedelta

API_KEY = "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba"
BASE_URL = "https://api-baseball.p.rapidapi.com/games"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-baseball.p.rapidapi.com"
}

def get_tomorrow_mlb_games():
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime('%Y-%m-%d')
    params = {"date": date_str, "league": "1"}  # Cambia "league" si es necesario
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        print("❌ Error al obtener partidos MLB:", response.text)
        return []

def analyze_mlb_game(game):
    teams = game.get("teams", {})
    home = teams.get("home", {}).get("name", "")
    away = teams.get("away", {}).get("name", "")
    match_str = f"{home} vs {away}"

    # Lógica de ejemplo, la mejoraremos con stats reales
    prediction = {
        "match": match_str,
        "pick": "Over 7.5 carreras",
        "confidence": "Media",
        "reason": f"Ambos equipos tienen buen promedio de hits recientes, valor en las líneas."
    }
    return prediction