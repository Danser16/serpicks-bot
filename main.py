# =======================
# SERPICKS – MAIN (OKC)
# =======================
from datetime import datetime, timedelta, date
import zoneinfo, sys, requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE, MAX_PICKS_PER_DAY, FALLBACK_IF_NO_VALUE
from core import analyze_football_for
from mlb_analysis import analyze_mlb_for

def send_to_telegram(text):
    if "REEMPLAZA_CON_TU_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN no configurado. Solo imprimo el mensaje.")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)

def fmt_pick(p, sport):
    dt_txt = p["dt_local"].strftime("%Y-%m-%d %H:%M")
    edge_pct = f"{(p['edge']*100):.1f}%" if p.get("edge") is not None else "N/A"
    base = (f"🏷️ {sport} | {p.get('league','')}\n"
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

def gather_picks_for(d: date):
    fut = analyze_football_for(d)
    mlb = analyze_mlb_for(d)
    all_picks = [("Fútbol", p) for p in fut] + [("MLB", p) for p in mlb]
    all_picks.sort(key=lambda x: (x[1].get('edge') if x[1].get('edge') is not None else -9), reverse=True)
    return all_picks[:MAX_PICKS_PER_DAY]

def build_message_for(d: date):
    header = f"🔥 SERPICKS – Mejores Picks ({d.strftime('%Y-%m-%d')})\n\n"
    all_picks = gather_picks_for(d)
    if not all_picks and not FALLBACK_IF_NO_VALUE:
        return header + "No hay picks con valor hoy."
    sections = [fmt_pick(p, sport) for sport, p in all_picks]

    # Parlay del día (si hay 2+ con edge positivo)
    parlay = [p for (_, p) in all_picks if (p.get('edge') or -1) > 0][:3]
    parlay_txt = "\n💼 Parlay (valor):\n" + "\n".join(
        [f"- {p['home']} vs {p['away']} | {p['type']} | {p['odds_amer']}"] ) if len(parlay) >= 2 else ""

    footer = "\n—\n⚠️ Apuestas responsables. Las probabilidades cambian; verifica alineaciones y clima."
    return header + "\n\n".join(sections) + parlay_txt + footer

def short_summary(d: date, tag: str):
    all_picks = gather_picks_for(d)
    total = len(all_picks)
    top_line = ""
    if total:
        s, p = all_picks[0]
        edge_pct = f"{(p['edge']*100):.1f}%" if p.get("edge") is not None else "N/A"
        top_line = f"\nTop: {s} — {p['home']} vs {p['away']} | {p['type']} | Edge {edge_pct}"
    return f"✅ {tag} listo para {d.isoformat()}.\nTotal picks candidatos: {total}.{top_line}"

if __name__ == "__main__":
    # Modos:
    #   python main.py analyze_tomorrow  -> analiza mañana, NOTIFICA (no envía)
    #   python main.py recheck_today     -> reanaliza hoy, NOTIFICA (no envía)
    #   python main.py send_today        -> analiza hoy y ENVÍA
    mode = sys.argv[1] if len(sys.argv) > 1 else "send_today"
    tz = zoneinfo.ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()

    if mode == "analyze_tomorrow":
        target = today + timedelta(days=1)
        msg = build_message_for(target)  # para logs
        print("[ANÁLISIS MAÑANA]\n", msg)
        send_to_telegram(short_summary(target, "Análisis nocturno"))
    elif mode == "recheck_today":
        msg = build_message_for(today)  # para logs
        print("[RE-CHECK HOY]\n", msg)
        send_to_telegram(short_summary(today, "Revisión matutina"))
    elif mode == "send_today":
        final_msg = build_message_for(today)
        print(final_msg)
        send_to_telegram(final_msg)
    else:
        print("Modo desconocido:", mode)