"""
datos_demo.py — Datos REALES recogidos el 10/06/2026 de fuentes públicas
(CBS, FOX, Yahoo, ESPN, FanDuel, bet365, Polymarket).

Sirven para que la app funcione SIN API key (modo DEMO) y para que veas el
formato. Cuando conectes The Odds API, estos datos se reemplazan por cuotas
en vivo automáticamente.

⚠️ Algunas cuotas de empate / over-under están ESTIMADAS donde la fuente no
publicaba el número exacto (marcadas abajo). Las de ganador (1X2 money line)
son las reales reportadas. Verifica siempre en tu casa antes de apostar.

Fechas en formato ISO (UTC aproximado).
"""

EVENTOS_DEMO = [
    # ---------------------- Mundial 2026 — Jornada 1 ----------------------
    {
        "id": "wc:Mexico-South Africa:2026-06-11",
        "deporte": "Fútbol — Mundial 2026",
        "local": "México", "visitante": "Sudáfrica",
        "fecha": "2026-06-11T19:00:00Z",
        "mercados": {
            "1x2": {"local": 1.42, "empate": 4.40, "visitante": 8.50},
            "total": {"linea": 2.5, "over": 2.00, "under": 1.80},  # under estimado (tendencia)
        },
    },
    {
        "id": "wc:Canada-Bosnia:2026-06-12",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Canadá", "visitante": "Bosnia",
        "fecha": "2026-06-12T19:00:00Z",
        "mercados": {
            "1x2": {"local": 1.83, "empate": 3.75, "visitante": 5.00},
        },
    },
    {
        "id": "wc:USA-Paraguay:2026-06-12",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Estados Unidos", "visitante": "Paraguay",
        "fecha": "2026-06-12T23:00:00Z",
        "mercados": {
            "1x2": {"local": 1.98, "empate": 3.65, "visitante": 4.50},
        },
    },
    {
        "id": "wc:Brazil-Morocco:2026-06-13",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Brasil", "visitante": "Marruecos",
        "fecha": "2026-06-13T22:00:00Z",
        "mercados": {
            "1x2": {"local": 1.69, "empate": 4.00, "visitante": 5.80},
        },
    },
    {
        "id": "wc:Spain-CapeVerde:2026-06-15",
        "deporte": "Fútbol — Mundial 2026",
        "local": "España", "visitante": "Cabo Verde",
        "fecha": "2026-06-15T16:00:00Z",
        "mercados": {  # empate y visitante estimados (España favorita aplastante)
            "1x2": {"local": 1.14, "empate": 7.00, "visitante": 17.0},
        },
    },
    {
        "id": "wc:France-Senegal:2026-06-16",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Francia", "visitante": "Senegal",
        "fecha": "2026-06-16T19:00:00Z",
        "mercados": {  # estimado a partir de su condición de 2ª favorita
            "1x2": {"local": 1.55, "empate": 4.00, "visitante": 6.00},
        },
    },
    {
        "id": "wc:Argentina-Algeria:2026-06-17",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Argentina", "visitante": "Argelia",
        "fecha": "2026-06-17T01:00:00Z",
        "mercados": {  # empate/visitante estimados (Argentina -290 a ganar grupo)
            "1x2": {"local": 1.30, "empate": 5.00, "visitante": 9.00},
        },
    },
    {
        "id": "wc:England-Croatia:2026-06-17",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Inglaterra", "visitante": "Croacia",
        "fecha": "2026-06-17T20:00:00Z",
        "mercados": {  # estimado (3ª favorita)
            "1x2": {"local": 1.70, "empate": 3.80, "visitante": 5.00},
        },
    },
    {
        "id": "wc:Portugal-DRCongo:2026-06-17",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Portugal", "visitante": "RD Congo",
        "fecha": "2026-06-17T17:00:00Z",
        "mercados": {  # estimado (Portugal muy favorita)
            "1x2": {"local": 1.25, "empate": 6.00, "visitante": 11.0},
        },
    },
    {
        "id": "wc:Colombia-Uzbekistan:2026-06-17",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Colombia", "visitante": "Uzbekistán",
        "fecha": "2026-06-17T22:00:00Z",
        "mercados": {  # estimado (Colombia favorita clara)
            "1x2": {"local": 1.50, "empate": 4.00, "visitante": 6.50},
        },
    },
    {
        "id": "wc:Brazil-Haiti:2026-06-19",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Brasil", "visitante": "Haití",
        "fecha": "2026-06-19T23:00:00Z",
        "mercados": {  # empate/visitante estimados (Brasil aplastante)
            "1x2": {"local": 1.10, "empate": 9.00, "visitante": 21.0},
        },
    },
    {
        "id": "wc:Germany-IvoryCoast:2026-06-20",
        "deporte": "Fútbol — Mundial 2026",
        "local": "Alemania", "visitante": "Costa de Marfil",
        "fecha": "2026-06-20T20:00:00Z",
        "mercados": {  # estimado (Alemania favorita Grupo E -270)
            "1x2": {"local": 1.30, "empate": 5.00, "visitante": 9.00},
        },
    },
    # ---------------------- NBA Finals (deporte sin empate) ----------------------
    {
        "id": "nba:Knicks-Spurs-G4:2026-06-10",
        "deporte": "NBA Finals 2026",
        "local": "New York Knicks", "visitante": "San Antonio Spurs",
        "fecha": "2026-06-10T23:00:00Z",
        "mercados": {  # money line Game 4 estimado (Knicks 2-1, juegan en casa)
            "1x2": {"local": 1.62, "empate": None, "visitante": 2.40},
        },
    },
]
