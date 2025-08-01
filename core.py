import os
import requests
from datetime import datetime
from telegram import Bot

# API-Football
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
ODDS_URL = "https://api-football-v1.p.rapidapi.com/v3/odds"
headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Ligas importantes
IMPORTANT_LEAGUES = [
    "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
    "Liga MX", "Eredivisie", "UEFA Champions League", "Leagues Cup"
]

# 🔍 Obtener partidos de hoy
def get_today_fixtures():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "timezone": "America/Mexico_City"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        matches = response.json().get("response", [])
        return [m for m in matches if m.get("league", {}).get("name", "") in IMPORTANT_LEAGUES]
    else:
        print("❌ Error fútbol:", response.text)
        return []

# 🔢 Obtener momios reales del fixture
def get_odds_for_fixture(fixture_id):
    params = {"fixture": fixture_id}
    response = requests.get(ODDS_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data["response"]:
            bookmakers = data["response"][0].get("bookmakers", [])
            if not bookmakers:
                return {}
            markets = bookmakers[0].get("bets", [])
            odds_data = {}
            for market in markets:
                name = market.get("name", "")
                values = market.get("values", [])
                if name == "Match Winner":
                    odds_data["1x2"] = {
                        "home": float(values[0]["odd"]),
                        "draw": float(values[1]["odd"]),
                        "away": float(values[2]["odd"])
                    }
                elif name == "Double Chance":
                    odds_data["doubleChance"] = {
                        val["value"]: float(val["odd"]) for val in values
                    }
                elif name == "Over/Under":
                    for val in values:
                        if val["value"] == "Over 2.5":
                            odds_data.setdefault("2.5", {})["over"] = float(val["odd"])
                        elif val["value"] == "Under 2.5":
                            odds_data.setdefault("2.5", {})["under"] = float(val["odd"])
            return odds_data
    return {}

# 🧠 Análisis por partido
def analyze_match_v3(match):
    home = match.get("teams", {}).get("home", {})
    away = match.get("teams", {}).get("away", {})
    home_team = home.get("name", "")
    away_team = away.get("name", "")
    fixture_id = match.get("fixture", {}).get("id")

    if not home_team or not away_team or not fixture_id:
        return None

    odds = get_odds_for_fixture(fixture_id)

    xg_home = xg_away = 1.1  # Supuesto si no hay datos

    try:
        stats = match.get("statistics", {})
        xg_home = float(stats["home"]["expected"]["goals"])
        xg_away = float(stats["away"]["expected"]["goals"])
    except:
        pass

    picks = []

    # 🏆 Ganador
    if "1x2" in odds:
        best = min(odds["1x2"].items(), key=lambda x: x[1])
        winner = {"home": "Gana local", "draw": "Empate", "away": "Gana visitante"}.get(best[0], "")
        picks.append({
            "tipo": "Ganador 1X2",
            "valor": 100 / best[1],
            "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* {winner}\n🔢 *Cuota:* {best[1]}\n🎯 *Probabilidad implícita:* {round(100 / best[1], 2)}%"
        })

    # 🛡 Doble oportunidad
    if "doubleChance" in odds:
        best = min(odds["doubleChance"].items(), key=lambda x: x[1])
        picks.append({
            "tipo": "Doble oportunidad",
            "valor": 100 / best[1],
            "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* Doble oportunidad {best[0]}\n🔢 *Cuota:* {best[1]}\n🎯 *Probabilidad implícita:* {round(100 / best[1], 2)}%"
        })

    # 🎯 Over/Under
    if "2.5" in odds:
        over_odds = odds["2.5"].get("over")
        under_odds = odds["2.5"].get("under")
        if over_odds:
            prob_over = 100 / over_odds
            picks.append({
                "tipo": "Over 2.5 goles",
                "valor": prob_over,
                "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* Over 2.5 goles\n🔢 *Cuota:* {over_odds}\n🧠 *xG:* {xg_home + xg_away:.2f}\n🎯 *Probabilidad implícita:* {round(prob_over, 2)}%"
            })
        if under_odds:
            prob_under = 100 / under_odds
            picks.append({
                "tipo": "Under 2.5 goles",
                "valor": prob_under,
                "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* Under 2.5 goles\n🔢 *Cuota:* {under_odds}\n🧠 *xG:* {xg_home + xg_away:.2f}\n🎯 *Probabilidad implícita:* {round(prob_under, 2)}%"
            })

    if not picks:
        return None

    # Elegir mejor pick
    best_pick = max(picks, key=lambda x: x["valor"])
    if best_pick["valor"] < 60:
        best_pick["text"] += "\n⚠️ *Valor bajo, pick de riesgo. Juega con cautela.*"
    else:
        best_pick["text"] += "\n✅ *Buena opción con valor aceptable.*"
    return best_pick["text"]

# 📤 Enviar picks a Telegram
def send_to_telegram(picks):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Faltan variables de entorno.")
        return

    if not picks:
        message = "⚠️ *No se encontraron picks sólidos para hoy.*\nSigue atento a los análisis. 📊"
    else:
        message = "🔥 *PICKS SERPICKS (Manual)* 🔥\n\n"
        for p in picks:
            message += f"{p}\n\n"
        message += "📈 *Apuesta con cabeza y disciplina.*\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]

    for chunk in chunks:
        data = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        response = requests.post(url, data=data)
        if response.ok:
            print("✅ Enviado a Telegram")
        else:
            print(f"❌ Telegram error: {response.text}")