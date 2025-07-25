import os
import requests
from datetime import datetime, timedelta
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# APIs de análisis
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

def get_tomorrow_fixtures():
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime('%Y-%m-%d')
    params = {"date": date_str, "timezone": "America/Mexico_City"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        print("❌ Error fútbol:", response.text)
        return []

def analyze_match(match):
    home = match.get("teams", {}).get("home", {}).get("name", "")
    away = match.get("teams", {}).get("away", {}).get("name", "")
    league = match.get("league", {}).get("name", "")

    if not home or not away:
        return None

    # 🔍 Lógica simple con ejemplo de confianza
    return {
        "match": f"{home} vs {away}",
        "pick": "Over 2.5 goles",
        "confidence": "Alta",
        "reason": f"Ambos equipos promedian más de 1.5 goles por partido en {league}. Valor en cuotas."
    }

def get_tomorrow_mlb_games():
    # Aquí se conectaría la API de MLB (ya configurada con tu key PRO)
    # Por ahora usamos ejemplo básico
    return [
        {"match": "Yankees vs Red Sox", "pick": "Over 7.5 carreras", "confidence": "Media", "reason": "Buen rendimiento ofensivo y lanzadores débiles"}
    ]

def analyze_mlb_game(game):
    return {
        "match": game["match"],
        "pick": game["pick"],
        "confidence": game["confidence"],
        "reason": game["reason"]
    }

def send_to_telegram(picks):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Faltan variables de entorno.")
        return

    message = "🔥 *PICKS SERPICKS* 🔥\n\n"
    for p in picks:
        message += f"🏟 {p['match']}\n📌 *Pick:* {p['pick']}\n🧠 {p['reason']}\n\n"
    message += "✅ *Apuesta con estrategia y disciplina.*\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}

    response = requests.post(url, data=data)
    print("✅ Enviado a Telegram" if response.ok else f"❌ Telegram error: {response.text}")

def update_google_sheets(picks):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("SERPICKS").sheet1
        for pick in picks:
            row = [datetime.now().strftime("%Y-%m-%d"), pick["match"], pick["pick"], pick["confidence"], pick["reason"]]
            sheet.append_row(row)
        print("📊 Datos guardados en Google Sheets.")
    except Exception as e:
        print("❌ Google Sheets error:", e)

def send_summary_if_needed():
    today = datetime.now()
    if today.weekday() == 6 or today.day == month_last_day(today):
        message = f"📊 *Resumen {'semanal' if today.weekday() == 6 else 'mensual'} completo listo.*\nRevisa tu hoja de Google Sheets para ver rendimiento."
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data)

def month_last_day(date):
    next_month = date.replace(day=28) + timedelta(days=4)
    return (next_month - timedelta(days=next_month.day)).day