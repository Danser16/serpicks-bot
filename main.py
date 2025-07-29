import os
from datetime import datetime
from core import (
    get_today_fixtures,
    analyze_match_v2,
    send_to_telegram,
    update_google_sheets_summary
)
from mlb_analysis import get_todays_mlb_games, analyze_mlb_game_v2

def main():
    print("🎯 Iniciando análisis experto de partidos del día...")

    # 1. Análisis de fútbol
    fixtures = get_today_fixtures()
    futbol_picks = []

    for match in fixtures:
        prediction = analyze_match_v2(match)
        if prediction:
            futbol_picks.append(prediction)

    # 2. Análisis de MLB
    mlb_games = get_todays_mlb_games()
    mlb_picks = []

    for game in mlb_games:
        pick = analyze_mlb_game_v2(game)
        if pick:
            mlb_picks.append(pick)

    # 3. Juntar y limitar a 10 picks máximo
    all_picks = futbol_picks + mlb_picks
    max_picks = 10
    selected_picks = all_picks[:max_picks]

    if selected_picks:
        print(f"✅ Enviando {len(selected_picks)} picks a Telegram...")
        print(f"Total de picks generados: {len(all_picks)}")
    for p in selected_picks:
    print(p)
        send_to_telegram(selected_picks)
    else:
        print("⚠️ No se generaron picks.")

    update_google_sheets_summary()