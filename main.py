import os
from datetime import datetime
from mlb_analysis import get_tomorrow_mlb_games, analyze_mlb_game
from core import get_tomorrow_fixtures, analyze_match, update_google_sheets
from core import get_tomorrow_fixtures, analyze_match, send_to_telegram

def main():
    matches = get_tomorrow_fixtures()
    expert_picks = []

    for match in matches:
        prediction = analyze_match(match)
        if prediction:
            expert_picks.append(prediction)

    send_to_telegram(expert_picks)


def run_full_analysis():
    print("🧠 Análisis completo iniciado...")

    # Fútbol
    fixtures = get_tomorrow_fixtures()
    main_leagues = [
        "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
        "Liga MX", "Eredivisie", "UEFA Champions League", "Leagues Cup"
    ]
    expert_picks = []
    for match in fixtures:
        if match["league"]["name"] in main_leagues:
            result = analyze_match_v2(match)
            expert_picks.append(result)

    # MLB
    mlb_games = get_tomorrow_mlb_games()
    for game in mlb_games[:3]:  # Tomar máximo 3 juegos con valor
        result = analyze_mlb_game(game)
        expert_picks.append(result)

    if expert_picks:
        print(f"✅ {len(expert_picks)} picks seleccionados (Fútbol + MLB):")
        for p in expert_picks:
            print(f"🏟️ {p['match']} | {p['pick']} ({p['confidence']})")
            print(f"🧠 {p['reason']}")
            print("-" * 40)
        update_google_sheets(expert_picks)
        print("📤 Picks enviados a Telegram (simulado)")
    else:
        print("⛔ No hay partidos con valor para mañana.")
        
def analyze_today_liga_mx():
    from core import get_todays_liga_mx_fixtures, analyze_match, send_to_telegram, update_google_sheets

    fixtures = get_todays_liga_mx_fixtures()
    expert_picks = []

    for match in fixtures:
        result = analyze_match(match)
        if result:
            expert_picks.append(result)

    expert_picks = expert_picks[:5]  # Máximo 5 picks con valor

    if expert_picks:
        print(f"✅ {len(expert_picks)} picks Liga MX encontrados:")
        for p in expert_picks:
            print(f"🏟 {p['match']}")
            print(f"📌 Pick: {p['pick']}")
            print(f"🧠 {p['reason']}")
            print("-" * 40)
        send_to_telegram(expert_picks)
        update_google_sheets(expert_picks)
    else:
        print("📭 No hubo picks con valor en Liga MX hoy.")
        
if __name__ == "__main__":
    analyze_today_liga_mx()
    
    from mlb_analysis import get_todays_mlb_games, analyze_mlb_game_v2
from core import send_to_telegram, update_google_sheets

def analyze_today_mlb():
    print("⚾ Analizando MLB de hoy...")
    games = get_todays_mlb_games()
    picks = []

    for game in games:
        result = analyze_mlb_game_v2(game)
        if result:
            picks.append(result)

    picks = picks[:5]  # Limitar picks por seguridad

    if picks:
        print(f"✅ {len(picks)} picks MLB seleccionados:")
        for p in picks:
            print(f"🏟 {p['match']} | {p['pick']}\n🧠 {p['reason']}\n")
        send_to_telegram(picks)
        update_google_sheets(picks)
    else:
        print("📭 No hubo picks con valor en MLB hoy.")