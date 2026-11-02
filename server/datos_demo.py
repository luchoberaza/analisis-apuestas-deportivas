"""
datos_demo.py — Datos REALES recogidos el 10/06/2026 (fuentes públicas: CBS, FOX,
Yahoo, ESPN, FanDuel, bet365, Polymarket). Solo se usan como respaldo cuando NO
hay API key o se agotaron los créditos. Con tu key, se reemplazan por cuotas en vivo.

⚠️ Algunas cuotas de empate/total están estimadas donde la fuente no publicaba el
número exacto. Verifica siempre antes de apostar.
"""

EVENTOS_DEMO = [
    # ---- Mundial 2026 ----
    {"categoria": "mundial", "deporte": "Fútbol", "local": "México", "visitante": "Sudáfrica",
     "fecha": "2026-06-11T19:00:00Z",
     "mercados": {"1x2": {"local": 1.42, "empate": 4.40, "visitante": 8.50},
                  "total": {"linea": 2.5, "over": 2.00, "under": 1.80}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Canadá", "visitante": "Bosnia",
     "fecha": "2026-06-12T19:00:00Z",
     "mercados": {"1x2": {"local": 1.83, "empate": 3.75, "visitante": 5.00}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Estados Unidos", "visitante": "Paraguay",
     "fecha": "2026-06-12T23:00:00Z",
     "mercados": {"1x2": {"local": 1.98, "empate": 3.65, "visitante": 4.50}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Brasil", "visitante": "Marruecos",
     "fecha": "2026-06-13T22:00:00Z",
     "mercados": {"1x2": {"local": 1.69, "empate": 4.00, "visitante": 5.80}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "España", "visitante": "Cabo Verde",
     "fecha": "2026-06-15T16:00:00Z",
     "mercados": {"1x2": {"local": 1.14, "empate": 7.00, "visitante": 17.0}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Francia", "visitante": "Senegal",
     "fecha": "2026-06-16T19:00:00Z",
     "mercados": {"1x2": {"local": 1.55, "empate": 4.00, "visitante": 6.00}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Argentina", "visitante": "Argelia",
     "fecha": "2026-06-17T01:00:00Z",
     "mercados": {"1x2": {"local": 1.30, "empate": 5.00, "visitante": 9.00}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Inglaterra", "visitante": "Croacia",
     "fecha": "2026-06-17T20:00:00Z",
     "mercados": {"1x2": {"local": 1.70, "empate": 3.80, "visitante": 5.00}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Portugal", "visitante": "RD Congo",
     "fecha": "2026-06-17T17:00:00Z",
     "mercados": {"1x2": {"local": 1.25, "empate": 6.00, "visitante": 11.0}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Colombia", "visitante": "Uzbekistán",
     "fecha": "2026-06-17T22:00:00Z",
     "mercados": {"1x2": {"local": 1.50, "empate": 4.00, "visitante": 6.50}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Brasil", "visitante": "Haití",
     "fecha": "2026-06-19T23:00:00Z",
     "mercados": {"1x2": {"local": 1.10, "empate": 9.00, "visitante": 21.0}}},
    {"categoria": "mundial", "deporte": "Fútbol", "local": "Alemania", "visitante": "Costa de Marfil",
     "fecha": "2026-06-20T20:00:00Z",
     "mercados": {"1x2": {"local": 1.30, "empate": 5.00, "visitante": 9.00}}},
    # ---- NBA Finals (sin empate) ----
    {"categoria": "nba", "deporte": "Baloncesto", "local": "New York Knicks", "visitante": "San Antonio Spurs",
     "fecha": "2026-06-10T23:00:00Z",
     "mercados": {"1x2": {"local": 1.62, "empate": None, "visitante": 2.40}}},
]


def eventos_de(categoria: str) -> list[dict]:
    return [dict(e) for e in EVENTOS_DEMO if e["categoria"] == categoria]
