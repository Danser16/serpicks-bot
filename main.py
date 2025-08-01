from core import get_today_fixtures, analyze_match_v3, send_to_telegram

def main():
    print("🔍 Obteniendo partidos de hoy...")
    fixtures = get_today_fixtures()
    print(f"📅 Partidos encontrados: {len(fixtures)}")

    picks = []

    for match in fixtures:
        try:
            pick = analyze_match_v3(match)
            if pick:
                picks.append(pick)
        except Exception as e:
            print(f"❌ Error analizando partido: {e}")

    print(f"✅ Total de picks generados: {len(picks)}")

    send_to_telegram(picks)

if __name__ == "__main__":
    main()