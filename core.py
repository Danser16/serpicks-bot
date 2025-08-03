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

# 🔢 Obtener momios del fixture
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

# 🧠 Análisis por partido (máx 2 picks variados)
def analyze_match_v4(match):
    home = match.get("teams", {}).get("home", {}).get("name", "")
    away = match.get("teams", {}).get("away", {}).get("name", "")
    fixture_id = match.get("fixture", {}).get("id")
    if not home or not away or not fixture_id:
        return None

    odds = get_odds_for_fixture(fixture_id)
    xg_home = xg_away = 1.1  # por si no hay stats

    try:
        stats = match.get("statistics", {})
        xg_home = float(stats["home"]["expected"]["goals"])
        xg_away = float(stats["away"]["expected"]["goals"])
    except:
        pass

    picks = []

    def add_pick(nombre, cuota, texto_base):
        if cuota:
            prob = round(100 / cuota, 2)
            status = "✅ Buena opción con valor aceptable." if prob >= 60 else "⚠️ Pick con valor bajo. Riesgo moderado."
            picks.append({
                "valor": prob,
                "texto": f"🏟 {home} vs {away}\n📌 *Pick:* {nombre}\n🔢 *Cuota:* {cuota}\n🎯 *Probabilidad implícita:* {prob}%\n{status}"
            })

    # Analizar diferentes mercados
    if "1x2" in odds:
        best = min(odds["1x2"].items(), key=lambda x: x[1])
        add_pick(f"Gana {best[0]}", best[1], "1X2")

    if "doubleChance" in odds:
        best = min(odds["doubleChance"].items(), key=lambda x: x[1])
        add_pick(f"Doble oportunidad {best[0]}", best[1], "Doble Oportunidad")

    if "2.5" in odds:
        o = odds["2.5"]
        if "over" in o:
            add_pick("Over 2.5 goles", o["over"], "Over goles")
        if "under" in o:
            add_pick("Under 2.5 goles", o["under"], "Under goles")

    if "corners" in odds:
        c = odds["corners"]
        if "over" in c:
            add_pick("Over 9.5 corners", c["over"], "Corners")
        if "under" in c:
            add_pick("Under 9.5 corners", c["under"], "Corners")

    if "cards" in odds:
        c = odds["cards"]
        if "over" in c:
            add_pick("Over 4.5 tarjetas", c["over"], "Tarjetas")
        if "under" in c:
            add_pick("Under 4.5 tarjetas", c["under"], "Tarjetas")

    if "handicap" in odds:
        for line, cuota in odds["handicap"].items():
            add_pick(f"Hándicap {line}", cuota, "Hándicap")

    if not picks:
        return None

    # Ordenar por valor y seleccionar máximo 2 picks variados
    picks = sorted(picks, key=lambda x: x["valor"], reverse=True)
    unique_types = set()
    final_picks = []

    for p in picks:
        tipo = p["texto"].split("📌")[1].split(":")[1].split()[0]
        if tipo not in unique_types:
            unique_types.add(tipo)
            final_picks.append(p["texto"])
        if len(final_picks) == 2:
            break

    return final_picks

# 📤 Enviar picks a Telegram
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