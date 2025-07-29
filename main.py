from core import (
    get_today_fixtures,
    analyze_match_v2,
    send_to_telegram,
    update_google_sheets_summary
)
from mlb_analysis import (
    get_todays_mlb_games,
    analyze_mlb_game_v2
)

def main():
    print("🎯 Iniciando análisis experto de partidos del día...")

    # 1. Análisis de fútbol
    fixtures = get_today_fixtures()
    print(f"🗓 Total de partidos de fútbol hoy: {len(fixtures)}")
    futbol_picks = []

    for match in fixtures:
        home = match.get("teams", {}).get("home", {}).get("name", "¿?")
        away = match.get("teams", {}).get("away", {}).get("name", "¿?")
        print(f"🔍 Analizando: {home} vs {away}")
        prediction = analyze_match_v2(match)
        if prediction:
            print("✅ PICK generado:", prediction["pick"])
            futbol_picks.append(prediction)
        else:
            print("❌ Sin valor en este partido.")

    # 2. Análisis de MLB
    mlb_games = get_todays_mlb_games()
    print(f"⚾ Total de partidos MLB hoy: {len(mlb_games)}")
    mlb_picks = []

    for game in mlb_games:
        home = game.get("teams", {}).get("home", {}).get("name", "¿?")
        away = game.get("teams", {}).get("away", {}).get("name", "¿?")
        print(f"🔍 Analizando: {home} vs {away}")
        pick = analyze_mlb_game_v2(game)
        if pick:
            print("✅ PICK generado:", pick["pick"])
            mlb_picks.append(pick)
        else:
            print("❌ Sin valor en este partido.")

    # 3. Juntar y limitar a 10 picks máximo
    all_picks = futbol_picks + mlb_picks
    max_picks = 10
    selected_picks = all_picks[:max_picks]

    if selected_picks:
        print(f"📤 Enviando {len(selected_picks)} picks a Telegram...")
        for p in selected_picks:
            print(p)
        send_to_telegram(selected_picks)
    else:
        print("⚠️ No se generaron picks.")

    # 4. (Opcional) Google Sheets - desactivado si no hay credenciales
    try:
        update_google_sheets_summary()
    except Exception as e:
        print(f"❌ Error Google Sheets: {e}")

if __name__ == "__main__":
    main()