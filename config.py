# =======================
# SERPICKS – CONFIG
# =======================
import os

# --- API KEYS (pon las tuyas o usa variables de entorno) ---
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba")  # tu key confirmada
API_BASEBALL_KEY = os.getenv("API_BASEBALL_KEY", "dcc826470cmsh81cc72c63fa493fp1daeb4jsndc68721088ba")  # plan PRO en RapidAPI

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "REEMPLAZA_CON_TU_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "REEMPLAZA_CON_TU_CHAT_ID")  # canal o grupo destino

# --- Opciones generales ---
TIMEZONE = os.getenv("SERPICKS_TZ", "America/Mexico_City")

# Ligas importantes (API-Football IDs/Names se manejan por nombre; el fetch filtra por league names)
IMPORTANT_LEAGUES = {
    "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
    "Liga MX", "Eredivisie", "UEFA Champions League", "Leagues Cup"
}

# Límites y umbrales
MAX_PICKS_PER_DAY = 10
MAX_PICKS_PER_MATCH = 3
MIN_EDGE_FOR_STRONG = 0.05     # >=5% edge -> “Fuerte”
MIN_EDGE_FOR_SOFT = 0.01       # 1–5% edge -> “Moderado”
FALLBACK_IF_NO_VALUE = True    # si no hay valor alto, igual mandar picks con advertencia

# Over/Under por defecto (si no hay mercado xG) -> líneas estándar
DEFAULT_GOALS_LINES = [2.5, 3.0]

# MLB Config
MLB_MAX_PICKS_PER_GAME = 2
MLB_DEFAULT_TOTALS = [7.5, 8.5, 9.0]