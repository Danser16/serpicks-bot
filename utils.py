# =======================
# SERPICKS – UTILS
# =======================
from math import isfinite

def decimal_to_american(dec):
    try:
        dec = float(dec)
        if dec <= 1 or not isfinite(dec):
            return None
        if dec >= 2.0:
            return f"+{int(round((dec - 1) * 100))}"
        # favorite
        return f"-{int(round(100 / (dec - 1)))}"
    except Exception:
        return None

def implied_prob_from_decimal(dec):
    try:
        dec = float(dec)
        if dec <= 1:
            return None
        return 1.0 / dec
    except Exception:
        return None

def edge(prob_estimated, dec_odds):
    """
    Edge = (prob_estimated * dec_odds) - 1
    >0 => valor positivo
    """
    if prob_estimated is None or dec_odds is None:
        return None
    try:
        dec_odds = float(dec_odds)
        return (prob_estimated * dec_odds) - 1.0
    except Exception:
        return None

def label_edge(e):
    if e is None:
        return "N/A"
    if e >= 0.10:
        return "MUY FUERTE"
    if e >= 0.05:
        return "Fuerte"
    if e >= 0.01:
        return "Moderado"
    if e > 0:
        return "Ligero"
    return "Sin valor"

def clamp(n, lo, hi):
    return max(lo, min(hi, n))