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

def get_todays_liga_mx_fixtures():
    today = datetime.now().strftime('%Y-%m-%d')
    params = {"date": today, "timezone": "America/Mexico_City"}
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        print("❌ Error obteniendo partidos de hoy")
        return []

    all_matches = response.json().get("response", [])
    liga_mx_matches = [m for m in all_matches if m.get("league", {}).get("name", "") == "Liga MX"]
    return liga_mx_matches
        

def analyze_match(match):
    import statistics

    league_name = match.get("league", {}).get("name", "")
    if "Liga MX" not in league_name:
        return None  # Solo Liga MX

    teams = match.get("teams", {})
    stats = match.get("teams", {})

    home_team = teams.get("home", {}).get("name", "")
    away_team = teams.get("away", {}).get("name", "")

    # Seguridad básica
    if not home_team or not away_team:
        return None

    # Goles promedio en últimos partidos
    home_stats = match.get("statistics", {}).get("home", {})
    away_stats = match.get("statistics", {}).get("away", {})

    # Promedios de goles marcados y recibidos
    try:
        home_goals_for = home_stats["goals"]["for"]["average"]["total"]
        away_goals_for = away_stats["goals"]["for"]["average"]["total"]
        home_goals_against = home_stats["goals"]["against"]["average"]["total"]
        away_goals_against = away_stats["goals"]["against"]["average"]["total"]
    except:
        return None

    # Calcular promedio general
    avg_total_goals = statistics.mean([
        float(home_goals_for or 0), float(away_goals_for or 0),
        float(home_goals_against or 0), float(away_goals_against or 0)
    ])

    # Lógica de apuesta según análisis
    if avg_total_goals > 3.0:
        pick = "Over 2.5 goles"
        reason = f"Promedio de goles combinado de ambos equipos es de {round(avg_total_goals, 2)}. Tendencia alta de goles en Liga MX."
    elif avg_total_goals < 2.0:
        pick = "Under 2.5 goles"
        reason = f"Equipos con tendencia baja de goles. Promedio combinado: {round(avg_total_goals, 2)}."
    else:
        return None  # No hay valor claro

    return {
        "match": f"{home_team} vs {away_team}",
        "pick": pick,
        "confidence": "Alta" if avg_total_goals > 3.0 or avg_total_goals < 2.0 else "Media",
        "reason": reason
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

    # 🔄 Dividir si supera el límite
    max_length = 4096
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]

    for msg in messages:
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        response = requests.post(url, data=data)
        if response.ok:
            print("✅ Enviado a Telegram")
        else:
            print(f"❌ Telegram error: {response.text}")

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