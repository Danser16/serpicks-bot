import os
import requests
from datetime import datetime

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

IMPORTANT_LEAGUES = [
    "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
    "Liga MX", "Eredivisie", "UEFA Champions League", "Leagues Cup"
]

def get_today_fixtures():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "timezone": "America/Mexico_City"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        matches = response.json().get("response", [])
        return [m for m in matches if any(liga in m.get("league", {}).get("name", "") for liga in IMPORTANT_LEAGUES)]
    else:
        print("❌ Error fútbol:", response.text)
        return []

def get_odds_for_fixture(fixture_id):
    params = {"fixture": fixture_id}
    response = requests.get(ODDS_URL, headers=headers, params=params)
    odds_data = {}

    if response.status_code == 200:
        data = response.json()
        if data["response"]:
            bookmakers = data["response"][0].get("bookmakers", [])
            if not bookmakers:
                return {}
            bets = bookmakers[0].get("bets", [])
            for bet in bets:
                name = bet.get("name", "")
                values = bet.get("values", [])
                if name == "Match Winner":
                    odds_data["1x2"] = {v["value"]: float(v["odd"]) for v in values}
                elif name == "Double Chance":
                    odds_data["doubleChance"] = {v["value"]: float(v["odd"]) for v in values}
                elif name == "Over/Under":
                    for v in values:
                        if v["value"] == "Over 2.5":
                            odds_data.setdefault("2.5", {})["over"] = float(v["odd"])
                        elif v["value"] == "Under 2.5":
                            odds_data.setdefault("2.5", {})["under"] = float(v["odd"])
                        elif v["value"] == "Over 9.5 corners":
                            odds_data.setdefault("corners", {})["over"] = float(v["odd"])
                        elif v["value"] == "Under 9.5 corners":
                            odds_data.setdefault("corners", {})["under"] = float(v["odd"])
                        elif v["value"] == "Over 4.5 cards":
                            odds_data.setdefault("cards", {})["over"] = float(v["odd"])
                        elif v["value"] == "Under 4.5 cards":
                            odds_data.setdefault("cards", {})["under"] = float(v["odd"])
                elif name == "Handicap":
                    for v in values:
                        if "+1" in v["value"] or "-1" in v["value"]:
                            odds_data.setdefault("handicap", {})[v["value"]] = float(v["odd"])
    return odds_data

def decimal_to_american(decimal_odds):
    if decimal_odds >= 2:
        return f"+{round((decimal_odds - 1) * 100)}"
    else:
        return f"-{round(100 / (decimal_odds - 1))}"

def analyze_match_v4(match):
    home = match.get("teams", {}).get("home", {}).get("name", "")
    away = match.get("teams", {}).get("away", {}).get("name", "")
    fixture_id = match.get("fixture", {}).get("id")
    date_str = match.get("fixture", {}).get("date", "")
    if not home or not away or not fixture_id or not date_str:
        return None

    # Formatear fecha y hora
    fixture_datetime = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
    formatted_datetime = fixture_datetime.strftime("%d %B %Y - %H:%M hrs")

    odds = get_odds_for_fixture(fixture_id)
    xg_home = xg_away = 1.1

    try:
        stats = match.get("statistics", {})
        xg_home = float(stats["home"]["expected"]["goals"])
        xg_away = float(stats["away"]["expected"]["goals"])
    except:
        pass

    total_expected_goals = round(xg_home + xg_away, 2)
    picks = []

    def add_pick(nombre, cuota, tipo):
        if cuota:
            prob = round(100 / cuota, 2)
            momio = decimal_to_american(cuota)
            status = "✅ Buena opción con valor aceptable." if prob >= 60 else "⚠️ Pick con valor bajo. Riesgo moderado."
            picks.append({
                "valor": prob,
                "tipo": tipo,
                "texto": f"🏟 {home} vs {away}\n🗓 {formatted_datetime}\n📌 *Pick:* {nombre}\n💰 *Momio:* {momio}\n🎯 *Probabilidad implícita:* {prob}%\n🧠 *Se esperan aproximadamente {total_expected_goals} goles en el partido.*\n{status}"
            })

    if "1x2" in odds:
        for k, v in odds["1x2"].items():
            if k in ["Home", "Draw", "Away"]:
                nombre = {"Home": "Gana local", "Draw": "Empate", "Away": "Gana visitante"}[k]
                add_pick(nombre, v, "1X2")

    if "doubleChance" in odds:
        for k, v in odds["doubleChance"].items():
            add_pick(f"Doble oportunidad {k}", v, "Doble")

    if "2.5" in odds:
        if "over" in odds["2.5"]:
            add_pick("Over 2.5 goles", odds["2.5"]["over"], "Goles")
        if "under" in odds["2.5"]:
            add_pick("Under 2.5 goles", odds["2.5"]["under"], "Goles")

    if "corners" in odds:
        if "over" in odds["corners"]:
            add_pick("Over 9.5 corners", odds["corners"]["over"], "Corners")
        if "under" in odds["corners"]:
            add_pick("Under 9.5 corners", odds["corners"]["under"], "Corners")

    if "cards" in odds:
        if "over" in odds["cards"]:
            add_pick("Over 4.5 tarjetas", odds["cards"]["over"], "Tarjetas")
        if "under" in odds["cards"]:
            add_pick("Under 4.5 tarjetas", odds["cards"]["under"], "Tarjetas")

    if "handicap" in odds:
        for k, v in odds["handicap"].items():
            add_pick(f"Hándicap {k}", v, "Handicap")

    if not picks:
        return None

    picks = sorted(picks, key=lambda x: x["valor"], reverse=True)
    tipos_usados = set()
    final_picks = []

    for p in picks:
        if p["tipo"] not in tipos_usados:
            final_picks.append(p["texto"])
            tipos_usados.add(p["tipo"])
        if len(final_picks) == 3:
            break

    return final_picks

def send_to_telegram(picks):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Faltan variables de entorno.")
        return

    if not picks:
        message = "⚠️ *No se encontraron picks sólidos para hoy.*\nSigue atento a los análisis. 📊"
    else:
        message = "🔥 *PICKS SERPICKS (Análisis completo)* 🔥\n\n"
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