# =======================
# SERPICKS – FOOTBALL CORE
# =======================
import requests
from datetime import datetime, timedelta, timezone
import zoneinfo
from config import API_FOOTBALL_KEY, IMPORTANT_LEAGUES, TIMEZONE, MAX_PICKS_PER_MATCH, DEFAULT_GOALS_LINES, MIN_EDGE_FOR_STRONG, MIN_EDGE_FOR_SOFT, FALLBACK_IF_NO_VALUE
from utils import implied_prob_from_decimal, decimal_to_american, edge, label_edge, clamp

HEADERS_FOOTBALL = {
    "x-rapidapi-key": API_FOOTBALL_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

def _tz():
    return zoneinfo.ZoneInfo(TIMEZONE)

def _localize(dt_str):
    # API-Football returns ISO times in UTC; convert to local TZ
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.astimezone(_tz())

def get_todays_fixtures():
    # fixtures by date (today) — filter by IMPORTANT_LEAGUES automatically
    today = datetime.now(timezone.utc).date()
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"date": today.isoformat()}
    r = requests.get(url, headers=HEADERS_FOOTBALL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("response", [])
    # Keep only important leagues
    fixtures = [f for f in data if f.get("league", {}).get("name") in IMPORTANT_LEAGUES]
    return fixtures

def _extract_decimal_odds(odds_data, market_key, outcome_key):
    """
    odds_data: markets from API-Football odds endpoint
    market_key: e.g., "Match Winner", "Double Chance", "Goals Over/Under"
    outcome_key: e.g., "Home", "Draw", "Away" or "1X", "12", "X2", "Over 2.5"
    """
    if not odds_data:
        return None
    for b in odds_data:
        for m in b.get("bookmakers", []):
            for mk in m.get("bets", []):
                if mk.get("name") == market_key:
                    for v in mk.get("values", []):
                        if v.get("value") == outcome_key and v.get("odd"):
                            try:
                                return float(v["odd"])
                            except Exception:
                                pass
    return None

def get_odds_for_fixture(fixture_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/odds"
    params = {"fixture": fixture_id, "bookmaker": 8}  # 8=Pinny si está disponible; puedes cambiar bookmaker
    r = requests.get(url, headers=HEADERS_FOOTBALL, params=params, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("response", [])

def estimate_goals_xg(stats_home, stats_away):
    """
    Sencillo: pondera xG recientes + forma (goals for) para sacar goles esperados totales.
    Si no hay xG, usa promedios de GF/GA de últimos 5.
    """
    xg_h = stats_home.get("xg_recent", 1.2)
    xg_a = stats_away.get("xg_recent", 1.1)
    gf_h = stats_home.get("gf5", 6) / 5.0
    gf_a = stats_away.get("gf5", 5) / 5.0
    ga_h = stats_home.get("ga5", 5) / 5.0
    ga_a = stats_away.get("ga5", 6) / 5.0

    exp_home = 0.6 * xg_h + 0.4 * (gf_h * 0.6 + (ga_a)*0.4)
    exp_away = 0.6 * xg_a + 0.4 * (gf_a * 0.6 + (ga_h)*0.4)
    total = clamp(exp_home + exp_away, 0.5, 5.0)
    return exp_home, exp_away, total

def get_recent_stats(team_id):
    # Placeholder simple: podrías enriquecer con endpoints /fixtures?team= & last=5
    # Aquí devolvemos stats estimados rápidos (evita múltiples llamadas para simplicidad).
    return {"xg_recent": 1.2, "gf5": 6, "ga5": 5}

def analyze_fixture(fix):
    fid = fix["fixture"]["id"]
    home = fix["teams"]["home"]["name"]
    away = fix["teams"]["away"]["name"]
    league = fix["league"]["name"]
    dt_local = _localize(fix["fixture"]["date"])
    stats_home = get_recent_stats(fix["teams"]["home"]["id"])
    stats_away = get_recent_stats(fix["teams"]["away"]["id"])
    exp_h, exp_a, exp_total = estimate_goals_xg(stats_home, stats_away)

    # Cargar momios
    odds_data = get_odds_for_fixture(fid)
    dec_home = _extract_decimal_odds(odds_data, "Match Winner", "Home")
    dec_draw = _extract_decimal_odds(odds_data, "Match Winner", "Draw")
    dec_away = _extract_decimal_odds(odds_data, "Match Winner", "Away")

    # Probabilidades “modelo” muy sencillas (mejorarlas es fácil: ELO/xG)
    # Favorece al equipo con mayor exp_goals
    total_x = exp_h + exp_a
    p_home = clamp(exp_h / total_x + 0.05, 0.05, 0.85)
    p_away = clamp(exp_a / total_x - 0.05, 0.05, 0.85)
    p_draw = clamp(1 - (p_home + p_away), 0.05, 0.5)

    picks = []

    # 1) Ganador (1X2) – elegir mejor edge
    cand = []
    for label, p, dec in [("Local", p_home, dec_home), ("Empate", p_draw, dec_draw), ("Visitante", p_away, dec_away)]:
        if dec:
            e = edge(p, dec)
            cand.append((label, p, dec, e))
    cand.sort(key=lambda x: (x[3] if x[3] is not None else -9), reverse=True)
    if cand:
        label, p, dec, e = cand[0]
        picks.append({
            "type": f"1X2 – {label}",
            "league": league,
            "home": home, "away": away,
            "dt_local": dt_local, "exp_goals": exp_total,
            "odds_dec": dec, "odds_amer": decimal_to_american(dec),
            "edge": e, "edge_label": label_edge(e),
            "note": "Valor fuerte" if (e or 0) >= MIN_EDGE_FOR_STRONG else ("Valor moderado" if (e or 0) >= MIN_EDGE_FOR_SOFT else "Valor bajo")
        })

    # 2) Doble oportunidad – asegura opciones si 1X2 no tiene valor
    dc_candidates = [
        ("1X", max(p_home + p_draw - 0.02, 0.0), _extract_decimal_odds(odds_data, "Double Chance", "1X")),
        ("12", max(p_home + p_away - 0.01, 0.0), _extract_decimal_odds(odds_data, "Double Chance", "12")),
        ("X2", max(p_draw + p_away - 0.02, 0.0), _extract_decimal_odds(odds_data, "Double Chance", "X2")),
    ]
    dc_candidates = [(k,p,dec, edge(p,dec) if dec else None) for (k,p,dec) in dc_candidates]
    dc_candidates = [c for c in dc_candidates if c[2]]
    dc_candidates.sort(key=lambda x: (x[3] if x[3] is not None else -9), reverse=True)
    if dc_candidates:
        k,p,dec,e = dc_candidates[0]
        picks.append({
            "type": f"Doble Oportunidad – {k}",
            "league": league, "home": home, "away": away,
            "dt_local": dt_local, "exp_goals": exp_total,
            "odds_dec": dec, "odds_amer": decimal_to_american(dec),
            "edge": e, "edge_label": label_edge(e),
            "note": "Seguro/consistente; útil para banca."
        })

    # 3) Over/Under goles según exp_total
    best_ou = None
    for line in DEFAULT_GOALS_LINES:
        # prob over por Poisson simplificada (proxy): cuanto más excede total la línea, mayor prob
        diff = exp_total - line
        p_over = clamp(0.50 + diff*0.18, 0.05, 0.90)  # pendiente sencilla
        p_under = 1 - p_over
        dec_over = _extract_decimal_odds(odds_data, "Goals Over/Under", f"Over {line}")
        dec_under = _extract_decimal_odds(odds_data, "Goals Over/Under", f"Under {line}")
        cands = []
        if dec_over: cands.append(("Over", line, p_over, dec_over, edge(p_over, dec_over)))
        if dec_under: cands.append(("Under", line, p_under, dec_under, edge(p_under, dec_under)))
        if cands:
            cands.sort(key=lambda x: (x[4] if x[4] is not None else -9), reverse=True)
            cand = cands[0]
            if best_ou is None or (cand[4] or -9) > (best_ou[4] or -9):
                best_ou = cand

    if best_ou:
        side, line, p, dec, e = best_ou
        picks.append({
            "type": f"{side} {line} goles",
            "league": league, "home": home, "away": away,
            "dt_local": dt_local, "exp_goals": exp_total,
            "odds_dec": dec, "odds_amer": decimal_to_american(dec),
            "edge": e, "edge_label": label_edge(e),
            "note": "Basado en goles esperados (xG/formas)."
        })

    # Limitar picks por partido
    return picks[:MAX_PICKS_PER_MATCH]

def analyze_today_football():
    fixtures = get_todays_fixtures()
    all_picks = []
    for f in fixtures:
        all_picks.extend(analyze_fixture(f))
    # Ordenar por edge descendente
    all_picks.sort(key=lambda x: (x["edge"] if x["edge"] is not None else -9), reverse=True)
    # Si nadie tiene buen valor y el flag permite, mantenemos “mejores disponibles”
    if not all_picks and FALLBACK_IF_NO_VALUE:
        return []
    return all_picks
    # --- Backwards-compat alias to avoid Railway crash ---
def analyze_football_for(day: str | None = None):
    """
    Compatibilidad con versiones anteriores.
    Ignora el parámetro y analiza los partidos de HOY.
    """
    return analyze_today_football()