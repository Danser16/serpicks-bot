from core import get_today_fixtures, analyze_match_v4, send_to_telegram

def main():
    print("🔍 Obteniendo partidos de hoy...")
    fixtures = get_today_fixtures()
    print(f"📅 Partidos encontrados: {len(fixtures)}")

    picks = []
    for match in fixtures:
        result = analyze_match_v4(match)
        if result:
            picks.extend(result)

    print(f"✅ Total de picks generados: {len(picks)}")
    send_to_telegram(picks)

if __name__ == "__main__":
    main()