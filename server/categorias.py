"""
categorias.py — Subcategorías de apuestas y su mapeo a las claves de The Odds API.

Cada categoría tiene: clave interna, nombre legible, sport_key de The Odds API,
deporte y si suele tener empate (fútbol sí, NBA/MLB no).

Lista de sport_keys: https://the-odds-api.com/sports-odds-data/sports-apis.html
(o ejecuta el endpoint /api/deportes de la app para ver las disponibles en vivo).
"""

CATEGORIAS = {
    # ---- Meta-categoría: agrega todo el fútbol activo ----
    "futbol": {
        "nombre": "⚽ Todo el fútbol", "grupo": "Destacado",
        "sport_key": None, "empate": True,
    },
    # ---- Fútbol: torneos ----
    "mundial": {
        "nombre": "Mundial 2026", "grupo": "Fútbol",
        "sport_key": "soccer_fifa_world_cup", "empate": True,
    },
    "libertadores": {
        "nombre": "Copa Libertadores", "grupo": "Fútbol",
        "sport_key": "soccer_conmebol_copa_libertadores", "empate": True,
    },
    "champions": {
        "nombre": "Champions League", "grupo": "Fútbol",
        "sport_key": "soccer_uefa_champs_league", "empate": True,
    },
    "sudamericana": {
        "nombre": "Copa Sudamericana", "grupo": "Fútbol",
        "sport_key": "soccer_conmebol_copa_sudamericana", "empate": True,
    },
    # ---- Fútbol: ligas (con sus nombres) ----
    "laliga": {
        "nombre": "LaLiga (España)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_spain_la_liga", "empate": True,
    },
    "premier": {
        "nombre": "Premier League (Inglaterra)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_epl", "empate": True,
    },
    "seriea": {
        "nombre": "Serie A (Italia)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_italy_serie_a", "empate": True,
    },
    "bundesliga": {
        "nombre": "Bundesliga (Alemania)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_germany_bundesliga", "empate": True,
    },
    "ligue1": {
        "nombre": "Ligue 1 (Francia)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_france_ligue_one", "empate": True,
    },
    "brasileirao": {
        "nombre": "Brasileirão (Brasil)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_brazil_campeonato", "empate": True,
    },
    "argentina": {
        "nombre": "Liga Profesional (Argentina)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_argentina_primera_division", "empate": True,
    },
    "ligamx": {
        "nombre": "Liga MX (México)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_mexico_ligamx", "empate": True,
    },
    "mls": {
        "nombre": "MLS (USA)", "grupo": "Ligas de fútbol",
        "sport_key": "soccer_usa_mls", "empate": True,
    },
    # ---- Otros deportes ----
    "nba": {
        "nombre": "NBA (baloncesto)", "grupo": "Otros deportes",
        "sport_key": "basketball_nba", "empate": False,
    },
    "mlb": {
        "nombre": "MLB (béisbol)", "grupo": "Otros deportes",
        "sport_key": "baseball_mlb", "empate": False,
    },
    "nfl": {
        "nombre": "NFL (fútbol americano)", "grupo": "Otros deportes",
        "sport_key": "americanfootball_nfl", "empate": False,
    },
    "tenis_atp": {
        "nombre": "Tenis ATP", "grupo": "Otros deportes",
        "sport_key": "tennis_atp_aus_open_singles", "empate": False,
    },
}

# Orden de los grupos para la UI
GRUPOS = ["Destacado", "Fútbol", "Ligas de fútbol", "Otros deportes"]


def info(categoria: str) -> dict | None:
    return CATEGORIAS.get(categoria)


def futbol_keys() -> list[str]:
    """Claves de todas las categorías de fútbol reales (para la meta-categoría)."""
    return [k for k, v in CATEGORIAS.items()
            if v["grupo"] in ("Fútbol", "Ligas de fútbol") and v["sport_key"]]


def listar_para_ui() -> list[dict]:
    """Devuelve la lista de categorías agrupada para los selectores del frontend."""
    out = []
    for grupo in GRUPOS:
        items = [{"clave": k, "nombre": v["nombre"]}
                 for k, v in CATEGORIAS.items() if v["grupo"] == grupo]
        out.append({"grupo": grupo, "categorias": items})
    return out
