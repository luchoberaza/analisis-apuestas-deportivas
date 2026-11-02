"""
proveedores.py — Obtención de eventos+cuotas con CACHÉ y control de créditos.

Estrategia para que el plan gratuito (500 créditos/mes de The Odds API) te sobre:
  • Cada respuesta se guarda en datos/cache/<categoria>.json con su hora.
  • Solo se vuelve a llamar a la API si el caché tiene más de CACHE_TTL_HORAS (8 por
    defecto) o si el usuario fuerza la actualización (forzar=True).
  • Se leen las cabeceras x-requests-remaining / x-requests-used que devuelve la API
    para saber siempre cuántos créditos quedan y mostrarlos en el dashboard.
  • Si no hay key o se agotaron los créditos → se usa el caché previo o los datos demo.
"""
from __future__ import annotations
import datetime as dt
import json
import statistics
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

import categorias
import datos_demo

BASE = "https://api.the-odds-api.com/v4"
CACHE_DIR = Path(__file__).resolve().parent.parent / "datos" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
#  Llamada cruda a The Odds API (devuelve datos + créditos)
# --------------------------------------------------------------------------- #
def _llamar_odds_api(api_key: str, sport_key: str, region: str = "eu") -> dict:
    params = {
        "apiKey": api_key, "regions": region,
        "markets": "h2h,totals", "oddsFormat": "decimal", "dateFormat": "iso",
    }
    url = f"{BASE}/sports/{sport_key}/odds/?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            datos = json.loads(r.read().decode("utf-8"))
            restantes = r.headers.get("x-requests-remaining")
            usados = r.headers.get("x-requests-used")
        return {
            "ok": True, "datos": datos,
            "creditos_restantes": int(restantes) if restantes else None,
            "creditos_usados": int(usados) if usados else None,
            "error": None,
        }
    except urllib.error.HTTPError as e:
        return {"ok": False, "datos": None, "creditos_restantes": None,
                "creditos_usados": None,
                "error": f"HTTP {e.code} de The Odds API ({e.reason}). "
                         f"{'Créditos agotados o key inválida.' if e.code in (401, 429) else ''}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "datos": None, "creditos_restantes": None,
                "creditos_usados": None, "error": f"Sin conexión: {e}"}


def deportes_activos(api_key: str) -> set | None:
    """Sport keys con eventos activos (endpoint /sports, NO consume créditos). Cache 1 h."""
    cache = _leer_cache("_sports", "activos")
    if cache and _edad_horas(cache["guardado"]) < 1.0:
        return set(cache["eventos"])
    try:
        url = f"{BASE}/sports/?apiKey={urllib.parse.quote(api_key)}&all=false"
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        keys = [d["key"] for d in data if d.get("active")]
        _guardar_cache("_sports", "activos",
                       {"guardado": dt.datetime.now(dt.timezone.utc).isoformat(), "eventos": keys})
        return set(keys)
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- #
#  Normalización al formato común de la app
# --------------------------------------------------------------------------- #
def _prom(vals: list[float]) -> float:
    return round(statistics.mean(vals), 3)


def _normalizar(crudo: list[dict], categoria: str) -> list[dict]:
    info = categorias.info(categoria) or {}
    deporte = info.get("grupo", "")
    out = []
    for ev in crudo:
        local, visitante = ev.get("home_team"), ev.get("away_team")
        if not local or not visitante:
            continue
        h2h = {"local": [], "empate": [], "visitante": []}
        tot = {"linea": None, "over": [], "under": []}
        for casa in ev.get("bookmakers", []):
            for mkt in casa.get("markets", []):
                if mkt["key"] == "h2h":
                    for o in mkt["outcomes"]:
                        if o["name"] == local:
                            h2h["local"].append(o["price"])
                        elif o["name"] == visitante:
                            h2h["visitante"].append(o["price"])
                        else:
                            h2h["empate"].append(o["price"])
                elif mkt["key"] == "totals":
                    for o in mkt["outcomes"]:
                        tot["linea"] = o.get("point")
                        if o["name"].lower() == "over":
                            tot["over"].append(o["price"])
                        elif o["name"].lower() == "under":
                            tot["under"].append(o["price"])
        mercados = {}
        if h2h["local"] and h2h["visitante"]:
            mercados["1x2"] = {
                "local": _prom(h2h["local"]),
                "empate": _prom(h2h["empate"]) if h2h["empate"] else None,
                "visitante": _prom(h2h["visitante"]),
            }
        if tot["over"] and tot["under"]:
            mercados["total"] = {"linea": tot["linea"],
                                 "over": _prom(tot["over"]), "under": _prom(tot["under"])}
        if not mercados:
            continue
        out.append({
            "categoria": categoria, "deporte": deporte,
            "local": local, "visitante": visitante,
            "fecha": ev["commence_time"], "mercados": mercados,
        })
    return out


# --------------------------------------------------------------------------- #
#  Caché en disco
# --------------------------------------------------------------------------- #
def _ruta_cache(categoria: str, region: str) -> Path:
    return CACHE_DIR / f"{categoria}_{region}.json"


def _leer_cache(categoria: str, region: str) -> dict | None:
    ruta = _ruta_cache(categoria, region)
    if not ruta.exists():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _guardar_cache(categoria: str, region: str, payload: dict) -> None:
    _ruta_cache(categoria, region).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _edad_horas(iso: str) -> float:
    t = dt.datetime.fromisoformat(iso)
    ahora = dt.datetime.now(dt.timezone.utc)
    return (ahora - t).total_seconds() / 3600.0


# --------------------------------------------------------------------------- #
#  API pública del módulo
# --------------------------------------------------------------------------- #
def _obtener_futbol(env: dict, region: str, ttl_horas: float, forzar: bool) -> dict:
    """Meta-categoría: agrega los partidos de todas las competiciones de fútbol ACTIVAS."""
    api_key = (env.get("ODDS_API_KEY") or "").strip()
    activos = deportes_activos(api_key) if api_key else None
    if activos is None and api_key:
        # Fallback prudente (si /sports falla) para no gastar créditos de más.
        activos = {"soccer_fifa_world_cup", "soccer_conmebol_copa_libertadores",
                   "soccer_uefa_champs_league", "soccer_conmebol_copa_sudamericana"}

    eventos, fuentes, creditos = [], set(), None
    for ck in categorias.futbol_keys():
        sk = categorias.info(ck)["sport_key"]
        if activos is not None and sk not in activos:
            continue  # competición en pausa: no se consulta (cero gasto)
        sub = obtener(ck, env, region, ttl_horas, forzar)
        for ev in sub["eventos"]:
            ev = dict(ev)
            ev["categoria_nombre"] = categorias.info(ck)["nombre"]
            ev["categoria_clave"] = ck
            eventos.append(ev)
        fuentes.add(sub["meta"].get("fuente"))
        if sub["meta"].get("creditos_restantes") is not None:
            creditos = sub["meta"]["creditos_restantes"]

    fuente = ("vivo" if "vivo" in fuentes else
              "cache" if "cache" in fuentes else
              "cache_viejo" if "cache_viejo" in fuentes else "demo")
    msg = (f"Todo el fútbol activo: {len(eventos)} partidos."
           if api_key else
           "Modo DEMO. Pega tu API key para ver todas las competiciones de fútbol en vivo.")
    return {"eventos": eventos, "meta": {
        "fuente": fuente, "categoria_nombre": "Todo el fútbol",
        "creditos_restantes": creditos, "edad_horas": None, "mensaje": msg}}


def obtener(categoria: str, env: dict, region: str = "eu",
            ttl_horas: float = 8.0, forzar: bool = False) -> dict:
    """
    Devuelve {eventos, meta}. meta incluye fuente, créditos, edad del caché y avisos.
    Orden de preferencia: caché fresco → API en vivo → caché viejo → demo.
    """
    api_key = (env.get("ODDS_API_KEY") or "").strip()
    info = categorias.info(categoria)
    if not info:
        return {"eventos": [], "meta": {"fuente": "error",
                "mensaje": f"Categoría desconocida: {categoria}"}}
    if categoria == "futbol":
        return _obtener_futbol(env, region, ttl_horas, forzar)
    sport_key = info["sport_key"]
    cache = _leer_cache(categoria, region)

    # 1) caché fresco
    if cache and not forzar and _edad_horas(cache["guardado"]) < ttl_horas:
        return {"eventos": cache["eventos"], "meta": {
            "fuente": "cache", "categoria_nombre": info["nombre"],
            "edad_horas": round(_edad_horas(cache["guardado"]), 1),
            "creditos_restantes": cache.get("creditos_restantes"),
            "mensaje": f"Datos del caché (hace {round(_edad_horas(cache['guardado']),1)} h). "
                       f"Se actualizan solos cada {ttl_horas:.0f} h o con 'Actualizar'."}}

    # 2) API en vivo (si hay key)
    if api_key:
        res = _llamar_odds_api(api_key, sport_key, region)
        if res["ok"]:
            eventos = _normalizar(res["datos"], categoria)
            payload = {"guardado": dt.datetime.now(dt.timezone.utc).isoformat(),
                       "eventos": eventos,
                       "creditos_restantes": res["creditos_restantes"]}
            _guardar_cache(categoria, region, payload)
            return {"eventos": eventos, "meta": {
                "fuente": "vivo", "categoria_nombre": info["nombre"],
                "edad_horas": 0.0,
                "creditos_restantes": res["creditos_restantes"],
                "creditos_usados": res["creditos_usados"],
                "mensaje": (f"Cuotas EN VIVO. Te quedan {res['creditos_restantes']} "
                            f"créditos este mes." if res["creditos_restantes"] is not None
                            else "Cuotas en vivo.")}}
        # 3) la API falló → caché viejo si existe
        if cache:
            return {"eventos": cache["eventos"], "meta": {
                "fuente": "cache_viejo", "categoria_nombre": info["nombre"],
                "edad_horas": round(_edad_horas(cache["guardado"]), 1),
                "creditos_restantes": cache.get("creditos_restantes"),
                "mensaje": f"⚠️ {res['error']} Mostrando últimos datos guardados "
                           f"(hace {round(_edad_horas(cache['guardado']),1)} h)."}}
        # sin caché: caer a demo abajo, anotando el error
        error_api = res["error"]
    else:
        error_api = "No hay ODDS_API_KEY configurada."

    # 4) demo (respaldo final)
    eventos = datos_demo.eventos_de(categoria)
    return {"eventos": eventos, "meta": {
        "fuente": "demo", "categoria_nombre": info["nombre"], "edad_horas": None,
        "creditos_restantes": None,
        "mensaje": (f"Modo DEMO (datos del 10/06/2026). {error_api} "
                    + ("Pega tu API key gratis en .env para datos en vivo de esta categoría."
                       if not eventos else
                       "No hay datos demo para esta categoría: necesitas API key."))}}
