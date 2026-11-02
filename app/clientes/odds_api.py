"""
clientes/odds_api.py — Conector a The Odds API (https://the-odds-api.com).

Plan gratis: 500 créditos/mes. Cada llamada a /odds consume créditos = nº de
mercados x nº de regiones. Por eso pedimos pocos mercados (h2h, totals) y una
sola región por llamada.

Devuelve eventos en el FORMATO NORMALIZADO común de la app:

    {
      "id": "<hash único del evento>",
      "deporte": "Fútbol — Mundial 2026",
      "local": "Mexico",
      "visitante": "South Africa",
      "fecha": "2026-06-11T19:00:00Z",
      "mercados": {
          "1x2":   {"local": 1.42, "empate": 4.40, "visitante": 8.50},
          "total": {"linea": 2.5, "over": 1.90, "under": 1.90},   # opcional
      },
    }

Si no hay API key o falla la red, las funciones lanzan RuntimeError y el
programa principal cae automáticamente al modo DEMO con datos reales guardados.
"""
from __future__ import annotations
import datetime as dt
import statistics
import urllib.request
import urllib.parse
import urllib.error
import json

BASE = "https://api.the-odds-api.com/v4"


def _get(url: str) -> list | dict:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"The Odds API respondió {e.code}: {e.reason}") from e
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"No se pudo conectar a The Odds API: {e}") from e


def listar_deportes(api_key: str) -> list[dict]:
    """Lista las claves de deporte disponibles (para saber qué puedes pedir)."""
    url = f"{BASE}/sports/?apiKey={urllib.parse.quote(api_key)}"
    return _get(url)


def _promedio_cuotas(valores: list[float]) -> float:
    """Promedia las cuotas de varias casas para un mismo resultado."""
    return round(statistics.mean(valores), 3)


def obtener_eventos(api_key: str, sport_key: str = "soccer_fifa_world_cup",
                    dias: int = 14, region: str = "eu") -> list[dict]:
    """
    Descarga eventos del deporte indicado con cuotas h2h (1X2) y totals (O/U),
    filtrando los que comienzan dentro de los próximos `dias` días.

    region: 'eu' (casas europeas), 'us', 'uk', 'au'.
    """
    params = {
        "apiKey": api_key,
        "regions": region,
        "markets": "h2h,totals",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
    }
    url = f"{BASE}/sports/{sport_key}/odds/?" + urllib.parse.urlencode(params)
    crudo = _get(url)

    limite = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=dias)
    eventos = []
    for ev in crudo:
        inicio = dt.datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00"))
        if inicio > limite:
            continue

        local = ev["home_team"]
        visitante = ev["away_team"]

        # agregamos cuotas de todas las casas por tipo de resultado
        h2h = {"local": [], "empate": [], "visitante": []}
        total = {"linea": None, "over": [], "under": []}
        for casa in ev.get("bookmakers", []):
            for mercado in casa.get("markets", []):
                if mercado["key"] == "h2h":
                    for o in mercado["outcomes"]:
                        if o["name"] == local:
                            h2h["local"].append(o["price"])
                        elif o["name"] == visitante:
                            h2h["visitante"].append(o["price"])
                        else:  # 'Draw'
                            h2h["empate"].append(o["price"])
                elif mercado["key"] == "totals":
                    for o in mercado["outcomes"]:
                        total["linea"] = o.get("point")
                        if o["name"].lower() == "over":
                            total["over"].append(o["price"])
                        elif o["name"].lower() == "under":
                            total["under"].append(o["price"])

        mercados = {}
        if h2h["local"] and h2h["visitante"]:
            mercados["1x2"] = {
                "local": _promedio_cuotas(h2h["local"]),
                "empate": _promedio_cuotas(h2h["empate"]) if h2h["empate"] else None,
                "visitante": _promedio_cuotas(h2h["visitante"]),
            }
        if total["over"] and total["under"]:
            mercados["total"] = {
                "linea": total["linea"],
                "over": _promedio_cuotas(total["over"]),
                "under": _promedio_cuotas(total["under"]),
            }

        if not mercados:
            continue

        eventos.append({
            "id": f"{sport_key}:{local}-{visitante}:{ev['commence_time'][:10]}",
            "deporte": sport_key,
            "local": local,
            "visitante": visitante,
            "fecha": ev["commence_time"],
            "mercados": mercados,
        })

    return eventos
