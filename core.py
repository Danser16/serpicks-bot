import os
import requests
import statistics
from datetime import datetime, timedelta
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

# 🔍 Obtener partidos de hoy
def get_today_fixtures():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "timezone": "America/Mexico_City"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("response", [])
    else:
        print("❌ Error fútbol:", response.text)
        return []

# 🧠 Análisis experto por partido
def analyze_match_v2(match):
    league = match.get("league", {}).get("name", "")
    home_team = match.get("teams", {}).get("home", {}).get("name", "")
    away_team = match.get("teams", {}).get("away", {}).get("name", "")

    if not home_team or not away_team:
        return None

    stats_home = match.get("statistics", {}).get("home", {})
    stats_away = match.get("statistics", {}).get("away", {})

    try:
        xg_home = float(stats_home["expected"]["goals"])
        xg_away = float(stats_away["expected"]["goals"])
        avg_gf_home = float(stats_home["goals"]["for"]["average"]["total"])
        avg_gf_away = float(stats_away["goals"]["for"]["average"]["total"])
        avg_ga_home = float(stats_home["goals"]["against"]["average"]["total"])
        avg_ga_away = float(stats_away["goals"]["against"]["average"]["total"])
    except:
        return None

    avg_total_goals = statistics.mean([avg_gf_home, avg_gf_away, avg_ga_home, avg_ga_away])
    avg_xg = xg_home + xg_away

    odds = match.get("odds", {}).get("2.5", {})
    over_odds = float(odds.get("over", 0))
    under_odds = float(odds.get("under", 0))

    if over_odds > 0:
        prob_over = round(100 / over_odds, 2)
    else:
        prob_over = 0

    if under_odds > 0:
        prob_under = round(100 / under_odds, 2)
    else:
        prob_under = 0

    # --- Lógica flexible para siempre mandar picks ---
    if avg_total_goals >= 2.5 or avg_xg >= 2.5:
        confidence = "Alta" if avg_total_goals >= 3 or avg_xg >= 3 else "Media"
        value_tag = "Valor ALTO" if prob_over < 60 else "Valor BAJO"
        return {
            "match": f"{home_team} vs {away_team}",
            "pick": "Over 2.5 goles",
            "confidence": confidence,
            "reason": f"xG: {avg_xg:.2f}, Goles promedio: {avg_total_goals:.2f}, Probabilidad implícita Over: {prob_over}%. {value_tag}."
        }

    if avg_total_goals < 2.2 and avg_xg < 2.2:
        confidence = "Alta" if avg_total_goals < 1.8 and avg_xg < 1.8 else "Media"
        value_tag = "Valor ALTO" if prob_under < 60 else "Valor BAJO"
        return {
            "match": f"{home_team} vs {away_team}",
            "pick": "Under 2.5 goles",
            "confidence": confidence,
            "reason": f"xG: {avg_xg:.2f}, Goles promedio: {avg_total_goals:.2f}, Probabilidad implícita Under: {prob_under}%. {value_tag}."
        }

    # Si no hay tendencia clara, se puede omitir
    return None

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
            message += f"🏟 {p['match']}\n📌 *Pick:* {p['pick']}\n🧠 {p['reason']}\n\n"
        message += "✅ *Apuesta con estrategia y disciplina.*\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    max_length = 4096
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]

    for msg in messages:
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
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