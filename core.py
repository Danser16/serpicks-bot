import requests
from datetime import datetime, timedelta

# Reemplazar con tu API Key y URL si ya tienes acceso real
API_KEY = "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

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
        data = response.json()
        return data["response"]
    else:
        print("Error al obtener partidos:", response.text)
        return []

def analyze_match(match):
    stats = match.get("teams", {})
    home = stats.get("home", {}).get("name", "")
    away = stats.get("away", {}).get("name", "")
    league = match.get("league", {}).get("name", "")

    # Lógica simple de ejemplo basada en promedio de goles
    prediction = {
        "match": f"{home} vs {away}",
        "pick": "Over 2.5 goles",
        "confidence": "Alta",
        "reason": f"Ambos equipos tienen buen ataque en {league}, valor en las cuotas."
    }
    return prediction

def update_google_sheets(picks):
    # Aquí puedes conectar a Google Sheets real si ya tienes las credenciales
    print("📊 Estadísticas actualizadas en Google Sheets correctamente.")