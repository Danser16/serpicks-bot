# =======================
# SERPICKS – MLB CORE
# =======================
import requests
from datetime import datetime, timezone
import zoneinfo
from config import API_BASEBALL_KEY, TIMEZONE, MLB_MAX_PICKS_PER_GAME, MLB_DEFAULT_TOTALS, MIN_EDGE_FOR_STRONG, MIN_EDGE_FOR_SOFT
from utils import decimal_to_american, implied_prob_from_decimal, edge, label_edge, clamp

HEADERS_MLB = {
    "x-rapidapi-key": API_BASEBALL_KEY,
    "x-rapidapi-host": "api-baseball.p.rapidapi.com"
}

def _tz():
    return zoneinfo.ZoneInfo(TIMEZONE)

def _localize(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.astimezone(_tz())

def get_today_games():
    url = "https://api-baseball.p.rapidapi.com/games"
    params = {"date": datetime.now(timezone.utc).date().isoformat(), "league": "MLB"}
    r = requests.get(url, headers=HEADERS_MLB, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_odds(game_id):
    url = "https://api-baseball.p.rapidapi.com/odds"
    params = {"game": game_id, "bookmaker": 8}
    r = requests.get(url, headers=HEADERS_MLB, params=params, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("response", [])

def _get_market(odds, name, value_key):
    if not odds:
        return None
    for x in odds:
        for bk in x.get("bookmakers", []):
            for bet in bk.get("bets", []):
                if bet.get("name") == name:
                    for v in bet.get("values", []):
                        if v.get("value") == value_key and v.get("odd"):
                            try:
                                return float(v["odd"])
                            except Exception:
                                pass
    return None

def quick_pitch_rating(team):
    # Muy simple: si existe ERA abridor, bullpen ERA; si no, defaults
    sp_era = team.get("probablePitcher", {}).get("era")
    try:
        sp_era = float(sp_era) if sp_era else 4.2
    except Exception:
        sp_era = 4.2
    bullpen = team.get("bullpenEra", 4.1)
    try:
        bullpen = float(bullpen)
    except Exception:
        bullpen = 4.1
    # rating más bajo = mejor
    return clamp(5.0 - ( (4.5 - sp_era)*0.8 + (4.3 - bullpen)*0.2 ), 2.0, 8.0)

def analyze_game(g):
    gid = g["id"]
    home = g["teams"]["home"]["name"]
    away = g["teams"]["away"]["name"]
    dt_local = _localize(g["date"])

    odds = get_odds(gid)
    dec_home = _get_market(odds, "Moneyline", "Home")
    dec_away = _get_market(odds, "Moneyline", "Away")
    dec_spread_home = _get_market(odds, "Spread", "Home -1.5")
    dec_spread_away = _get_market(odds, "Spread", "Away -1.5")

    # Ratings rápidos por pitcheo/bullpen (placeholder; mejora posible con stats reales)
    rate_home = quick_pitch_rating(g.get("teams", {}).get("home", {}))
    rate_away = quick_pitch_rating(g.get("teams", {}).get("away", {}))

    # Convertir a prob (más bajo mejor) -> home adv
    base_h = 1.0 / (rate_home + 0.001)
    base_a = 1.0 / (rate_away + 0.001)
    # ventaja local
    base_h *= 1.05

    s = base_h + base_a
    p_home = clamp(base_h / s, 0.35, 0.70)
    p_away = clamp(base_a / s, 0.30, 0.65)

    picks = []

    # ML mejor edge
    ml_cands = []
    if dec_home: ml_cands.append(("ML Home", p_home, dec_home))
    if dec_away: ml_cands.append(("ML Away", p_away, dec_away))
    ml_cands = [(k,p,dec, edge(p,dec)) for (k,p,dec) in ml_cands]
    ml_cands.sort(key=lambda x: (x[3] if x[3] is not None else -9), reverse=True)
    if ml_cands:
        k,p,dec,e = ml_cands[0]
        picks.append({
            "type": k, "home": home, "away": away, "dt_local": dt_local,
            "odds_dec": dec, "odds_amer": decimal_to_american(dec),
            "edge": e, "edge_label": label_edge(e),
            "note": "Basado en abridor/bullpen y ventaja local."
        })

    # Spread -1.5 del favorito si su prob > 58%
    if p_home > 0.58 and dec_spread_home:
        e = edge(p_home*0.55, dec_spread_home)  # aprox prob cubrir -1.5
        picks.append({
            "type": "Spread Home -1.5", "home": home, "away": away, "dt_local": dt_local,
            "odds_dec": dec_spread_home, "odds_amer": decimal_to_american(dec_spread_home),
            "edge": e, "edge_label": label_edge(e),
            "note": "Favorito con buena prob de cubrir."
        })
    if p_away > 0.58 and dec_spread_away:
        e = edge(p_away*0.55, dec_spread_away)
        picks.append({
            "type": "Spread Away -1.5", "home": home, "away": away, "dt_local": dt_local,
            "odds_dec": dec_spread_away, "odds_amer": decimal_to_american(dec_spread_away),
            "edge": e, "edge_label": label_edge(e),
            "note": "Favorito con buena prob de cubrir."
        })

    # Totales aproximados según rating de pitcheo
    # Línea estimada (menor rating -> menos carreras)
    est_total = clamp(9.0 - ( (5.5 - rate_home) + (5.5 - rate_away) )*0.6, 6.5, 11.5)
    best_tot = None
    for line in MLB_DEFAULT_TOTALS:
        diff = est_total - line
        p_over = clamp(0.5 + diff*0.15, 0.10, 0.90)
        p_under = 1 - p_over
        dec_over = _get_market(odds, "Totals", f"Over {line}")
        dec_under = _get_market(odds, "Totals", f"Under {line}")
        cands = []
        if dec_over: cands.append(("Over", line, p_over, dec_over, edge(p_over, dec_over)))
        if dec_under: cands.append(("Under", line, p_under, dec_under, edge(p_under, dec_under)))
        if cands:
            cands.sort(key=lambda x: (x[4] if x[4] is not None else -9), reverse=True)
            cand = cands[0]
            if best_tot is None or (cand[4] or -9) > (best_tot[4] or -9):
                best_tot = cand
    if best_tot:
        side, line, p, dec, e = best_tot
        picks.append({
            "type": f"{side} {line} carreras", "home": home, "away": away, "dt_local": dt_local,
            "odds_dec": dec, "odds_amer": decimal_to_american(dec),
            "edge": e, "edge_label": label_edge(e),
            "note": "Modelado por abridor/bullpen."
        })

    # Limitar picks del juego
    picks.sort(key=lambda x: (x["edge"] if x["edge"] is not None else -9), reverse=True)
    return picks[:MLB_MAX_PICKS_PER_GAME]

def analyze_today_mlb():
    games = get_today_games()
    allp = []
    for g in games:
        allp.extend(analyze_game(g))
    allp.sort(key=lambda x: (x["edge"] if x["edge"] is not None else -9), reverse=True)
    return allp