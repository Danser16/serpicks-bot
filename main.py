# =======================
# SERPICKS – MAIN
# =======================
from datetime import datetime
import zoneinfo
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE, MAX_PICKS_PER_DAY, FALLBACK_IF_NO_VALUE
from core import analyze_today_football
from mlb_analysis import analyze_today_mlb

def fmt_pick(p, sport):
    dt = p["dt_local"]
    dt_txt = dt.strftime("%Y-%m-%d %H:%M")
    edge_pct = f"{(p['edge']*100):.1f}%" if p.get("edge") is not None else "N/A"
    base = (f"🏷️ {sport} | {p.get('league', '')}\n"
            f"🗓️ {dt_txt}\n"
            f"⚔️ {p['home']} vs {p['away']}\n"
            f"🎯 Pick: {p['type']}\n"
            f"💵 Momio: {p['odds_amer']} (dec {p['odds_dec']})\n"
            f"📊 Edge: {edge_pct} ({p['edge_label']})\n")
    if sport == "Fútbol":
        base += f"🔮 Goles esperados: {p['exp_goals']:.2f}\n"
    if p.get("note"):
        base += f"📝 Nota: {p['note']}\n"
    return base

def build_message():
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    header = f"🔥 SERPICKS – Mejores Picks (hoy {datetime.now(tz).strftime('%Y-%m-%d')})\n\n"
    picks_fut = analyze_today_football()
    picks_mlb = analyze_today_mlb()

    # Merge y limitar total
    all_picks = []
    for p in picks_fut:
        all_picks.append(("Fútbol", p))
    for p in picks_mlb:
        all_picks.append(("MLB", p))

    # Orden por edge y recorte global
    all_picks.sort(key=lambda x: (x[1]['edge'] if x[1].get('edge') is not None else -9), reverse=True)
    if not all_picks and not FALLBACK_IF_NO_VALUE:
        return header + "No hay picks con valor hoy."
    all_picks = all_picks[:MAX_PICKS_PER_DAY]

    sections = []
    for sport, p in all_picks:
        sections.append(fmt_pick(p, sport))

    # Parlay del día (opcional): tomar 2–3 picks con mejor edge positivo
    parlay = [p for (_,p) in all_picks if (p.get('edge') or -1) > 0][:3]
    parlay_txt = ""
    if len(parlay) >= 2:
        parlay_txt = "\n💼 Parlay (valor):\n" + "\n".join([f"- {pi['home']} vs {pi['away']} | {pi['type']} | {pi['odds_amer']}" for pi in parlay])

    footer = "\n—\n⚠️ Apuestas responsables. Las probabilidades cambian; verifica alineaciones y clima cerca del inicio."
    return header + "\n\n".join(sections) + parlay_txt + footer

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    msg = build_message()
    print(msg)  # útil para logs
    try:
        if "REEMPLAZA_CON_TU_TOKEN" not in TELEGRAM_BOT_TOKEN:
            send_to_telegram(msg)
    except Exception as e:
        print("Error enviando a Telegram:", e)