import os
import requests
from datetime import datetime
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# API-Football
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Ligas importantes
IMPORTANT_LEAGUES = [
    "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Liga MX",
    "Eredivisie", "UEFA Champions League", "Leagues Cup"
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

# 🧠 Análisis experto por partido (1 sola apuesta)
def analyze_match_v3(match):
    home = match.get("teams", {}).get("home", {})
    away = match.get("teams", {}).get("away", {})
    home_team = home.get("name", "")
    away_team = away.get("name", "")
    league = match.get("league", {}).get("name", "")

    if not home_team or not away_team:
        return None

    odds = match.get("odds", {})
    xg_home = xg_away = 1.1  # Suponemos si no hay datos

    try:
        stats = match.get("statistics", {})
        xg_home = float(stats["home"]["expected"]["goals"])
        xg_away = float(stats["away"]["expected"]["goals"])
    except:
        pass

    picks = []

    # 1X2 (Ganador)
    if "1x2" in odds:
        best = min(odds["1x2"].items(), key=lambda x: x[1])
        winner = {"home": "Gana local", "draw": "Empate", "away": "Gana visitante"}.get(best[0], "")
        picks.append({
            "tipo": "Ganador 1X2",
            "valor": 100 / best[1],
            "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* {winner}\n🔢 *Cuota:* {best[1]}\n🎯 *Probabilidad implícita:* {round(100 / best[1], 2)}%"
        })

    # Doble oportunidad
    if "doubleChance" in odds:
        best = min(odds["doubleChance"].items(), key=lambda x: x[1])
        picks.append({
            "tipo": "Doble oportunidad",
            "valor": 100 / best[1],
            "text": f"🏟 {home_team} vs {away_team}\n📌 *Pick:* Doble oportunidad {best[0]}\n🔢 *Cuota:* {best[1]}\n🎯 *Probabilidad implícita:* {round(100 / best[1], 2)}%"
        })

    # Over/Under goles
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

    # Elegimos el pick con mayor probabilidad (menor riesgo)
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
        message = "⚠️ *No se encontraron picks sólidos para hoy.*\nAún así, sigue revisando estadísticas y mantente atento. 📊"
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

# 📊 Guardar picks en Google Sheets
def update_google_sheets_summary():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("SERPICKS").sheet1
        now = datetime.now().strftime("%Y-%m-%d")
        sheet.append_row([now, "Auto-run", "Manual execution ran", "", ""])
        print("📊 Registro guardado en Sheets.")
    except Exception as e:
        print("❌ Error Google Sheets:", e)