import os
from datetime import datetime
from core import (
    get_today_fixtures,
    analyze_match_v2,
    send_to_telegram,
    update_google_sheets_summary
)
from mlb_analysis import get_today_mlb_games, analyze_mlb_game_v2

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
    mlb_games = get_today_mlb_games()
    mlb_picks = []

    for game in mlb_games:
        pick = analyze_mlb_game_v2(game)
        if pick:
            mlb_picks.append(pick)

    # 3. Juntar picks y enviarlos
    all_picks = futbol_picks + mlb_picks

    if all_picks:
        print(f"✅ {len(all_picks)} picks generados, enviando a Telegram...")
        send_to_telegram(all_picks)
    else:
        print("⚠️ No se generaron picks para hoy. Revisa si hay partidos activos.")

    # 4. Actualizar hoja de cálculo (resumen diario)
    update_google_sheets_summary()

if __name__ == "__main__":
    main()