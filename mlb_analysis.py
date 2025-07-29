import os
import requests
from datetime import datetime

API_KEY = os.getenv("API_BASEBALL_KEY") or "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba"
BASE_URL = "https://api-baseball.p.rapidapi.com/games"
STATS_URL = "https://api-baseball.p.rapidapi.com/teams/statistics"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-baseball.p.rapidapi.com"
}

# 🔍 Obtener partidos MLB del día
def get_todays_mlb_games():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "league": "1", "season": "2024"}  # Liga 1 = MLB
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        print("❌ Error al obtener partidos MLB:", response.text)
        return []

# 📊 Obtener estadísticas de un equipo
def get_team_stats(team_id):
    params = {"team": team_id, "season": "2024", "league": "1"}
    response = requests.get(STATS_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("response", {})
    else:
        return {}

# 🧠 Análisis real del partido MLB
def analyze_mlb_game_v2(game):
    home = game["teams"]["home"]
    away = game["teams"]["away"]
    home_name = home["name"]
    away_name = away["name"]
    home_id = home["id"]
    away_id = away["id"]

    # 1. Obtener stats de ambos equipos
    stats_home = get_team_stats(home_id)
    stats_away = get_team_stats(away_id)

    if not stats_home or not stats_away:
        return None

    try:
        avg_runs_home = float(stats_home["runs"]["average"])
        avg_runs_away = float(stats_away["runs"]["average"])
        recent_form_home = stats_home["form"]
        recent_form_away = stats_away["form"]
    except:
        return None

    total_avg_runs = avg_runs_home + avg_runs_away
    pick = None
    reason = ""
    confidence = "Media"
    value_tag = ""

    # 2. Lógica de Over/Under
    if total_avg_runs >= 9.0:
        pick = "Over 8.5 carreras"
        confidence = "Alta" if total_avg_runs >= 10 else "Media"
        value_tag = "Valor ALTO" if total_avg_runs >= 9.5 else "Valor BAJO"
        reason = f"Promedio combinado: {total_avg_runs:.2f} carreras. {home_name} y {away_name} con tendencia ofensiva. {value_tag}."

    elif total_avg_runs <= 6.5:
        pick = "Under 7.5 carreras"
        confidence = "Alta" if total_avg_runs <= 6 else "Media"
        value_tag = "Valor ALTO" if total_avg_runs <= 6 else "Valor BAJO"
        reason = f"Ambos equipos anotan poco. Promedio combinado: {total_avg_runs:.2f} carreras. {value_tag}."

    # 3. Lógica de ganador (si no hay valor en Over/Under)
    if not pick:
        pick = f"Gana {home_name if avg_runs_home > avg_runs_away else away_name}"
        confidence = "Media"
        reason = f"{home_name}: {avg_runs_home:.2f} carreras por juego, {away_name}: {avg_runs_away:.2f}. Tendencia ofensiva favorable."
        value_tag = "Valor BAJO"

    return {
        "match": f"{home_name} vs {away_name}",
        "pick": pick,
        "confidence": confidence,
        "reason": f"{reason}"
    }