# =======================
# SERPICKS – MAIN (OKC)
# =======================
from datetime import datetime, timedelta, date
import zoneinfo, sys, requests

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE,
    MAX_PICKS_PER_DAY, FALLBACK_IF_NO_VALUE
)

# ---- Imports robustos (soporta nombres viejos/nuevos) ----
try:
    from core import analyze_football_for
except Exception:
    try:
        from core import analyze_today_football as analyze_football_for
    except Exception:
        def analyze_football_for(*args, **kwargs):
            return []

try:
    from mlb_analysis import analyze_mlb_for
except Exception:
    try:
        from mlb_analysis import analyze_today_mlb as analyze_mlb_for
    except Exception:
        def analyze_mlb_for(*args, **kwargs):
            return []

# ----------------- Utilidades -----------------
def _tz():
    return zoneinfo.ZoneInfo(TIMEZONE)

def send_to_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or "REEMPLAZA_CON_TU_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN no configurado. Solo imprimo el mensaje.\n")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=30)
    try:
        r.raise_for_status()
    except Exception as e:
        print("WARN telegram:", e, file=sys.stderr)

def _safe_dt_str(dt_obj):
    try:
        return dt_obj.astimezone(_tz()).strftime("%Y-%m-%d %H:%M")
    except Exception:
        try:
            return dt_obj.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(dt_obj)

def fmt_pick(p: dict, sport: str):
    dt_txt = _safe_dt_str(p.get("dt_local"))
    edge_val = p.get("edge")
    edge_pct = f"{edge_val*100:.1f}%" if edge_val is not None else "N/A"
    edge_label = p.get("edge_label", "")
    league = p.get("league", "MLB" if sport == "MLB" else "")

    base = (
        f"🏷️ {sport} | {league}\n"
        f"🗓️ {dt_txt}\n"
        f"⚔️ {p.get('home','')} vs {p.get('away','')}\n"
        f"🎯 Pick: {p.get('type','')}\n"
        f"💵 Momio: {p.get('odds_amer','')} (dec {p.get('odds_dec','')})\n"
        f"📊 Edge: {edge_pct}" + (f" ({edge_label})" if edge_label else "") + "\n"
    )
    if sport == "Fútbol" and "exp_goals" in p:
        base += f"🔮 Goles esperados: {p['exp_goals']:.2f}\n"
    if p.get("note"):
        base += f"📝 Nota: {p['note']}\n"
    return base

# ----------------- Orquestación -----------------
def gather_picks_for(d: date):
    all_picks = []

    # Fútbol
    try:
        fut = analyze_football_for(d) or []
        all_picks += [("Fútbol", p) for p in fut]
    except Exception as e:
        print("WARN fútbol:", e, file=sys.stderr)

    # MLB
    try:
        mlb = analyze_mlb_for(d) or []
        all_picks += [("MLB", p) for p in mlb]
    except Exception as e:
        print("WARN MLB:", e, file=sys.stderr)

    # Orden por edge
    all_picks.sort(key=lambda x: (x[1].get('edge') if x[1].get('edge') is not None else -9), reverse=True)
    return all_picks[:MAX_PICKS_PER_DAY]

def build_message_for(d: date):
    header = f"🔥 SERPICKS – Mejores Picks ({d.strftime('%Y-%m-%d')})\n\n"
    all_picks = gather_picks_for(d)

    if not all_picks:
        if FALLBACK_IF_NO_VALUE:
            return header + "No hay picks con valor alto. Mostrando mejores disponibles.\n"
        return header + "No hay picks con valor hoy."

    sections = [fmt_pick(p, sport) for sport, p in all_picks]

    # Parlay del día (si hay 2+ con edge positivo)
    parlay = [p for (_, p) in all_picks if (p.get('edge') or -1) > 0][:3]
    parlay_txt = ""
    if len(parlay) >= 2:
        parlay_txt = "\n💼 Parlay (valor):\n" + "\n".join(
            [f"- {p.get('home','')} vs {p.get('away','')} | {p.get('type','')} | {p.get('odds_amer','')}"
             for p in parlay]
        )

    footer = "\n—\n⚠️ Apuestas responsables. Las probabilidades cambian; verifica alineaciones y clima."
    return header + "\n".join(sections) + parlay_txt + footer

def short_summary(d: date, tag: str):
    all_picks = gather_picks_for(d)
    total = len(all_picks)
    top_line = ""
    if total:
        sport, p = all_picks[0]
        edge = p.get("edge")
        edge_pct = f"{edge*100:.1f}%" if edge is not None else "N/A"
        top_line = f"\nTop: {sport} — {p.get('home','')} vs {p.get('away','')} | {p.get('type','')} | Edge {edge_pct}"
    return f"✅ {tag} listo para {d.isoformat()}.\nTotal picks candidatos: {total}.{top_line}"

# ----------------- Entry point -----------------
if __name__ == "__main__":
    # Modos:
    #   python main.py analyze_tomorrow  -> analiza mañana, NOTIFICA (no envía picks)
    #   python main.py recheck_today     -> reanaliza hoy, NOTIFICA (no envía picks)
    #   python main.py send_today        -> analiza hoy y ENVÍA picks
    mode = sys.argv[1] if len(sys.argv) > 1 else "send_today"
    tz = _tz()
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