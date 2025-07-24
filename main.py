
import os
from datetime import datetime
from mlb_analysis import get_tomorrow_mlb_games, analyze_mlb_game
from core import get_tomorrow_fixtures, analyze_match, update_google_sheets

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
            result = analyze_match(match)
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
