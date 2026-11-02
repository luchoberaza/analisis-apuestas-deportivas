"""
apifootball.py — Cliente de API-Football (https://www.api-football.com) para datos
ricos por partido: historial (H2H), forma reciente y logos de equipos.

Acceso directo (api-sports.io) con cabecera 'x-apisports-key'. Plan free: 100/día.
Para no quemarlo: TODO se cachea en disco con TTL largo (24 h) y solo se llama
cuando el usuario abre un partido concreto (lazy). Si algo falla, no rompe nada.
"""
from __future__ import annotations
import datetime as dt
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

import banderas

HOST = "https://v3.football.api-sports.io"
CACHE = Path(__file__).resolve().parent.parent / "datos" / "cache" / "apifootball"
CACHE.mkdir(parents=True, exist_ok=True)
TTL_HORAS = 24.0


def _cache_get(nombre: str):
    f = CACHE / f"{nombre}.json"
    if not f.exists():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        edad = (dt.datetime.now(dt.timezone.utc)
                - dt.datetime.fromisoformat(d["_t"])).total_seconds() / 3600
        return d["v"] if edad < TTL_HORAS else None
    except Exception:  # noqa: BLE001
        return None


def _cache_set(nombre: str, valor) -> None:
    (CACHE / f"{nombre}.json").write_text(
        json.dumps({"_t": dt.datetime.now(dt.timezone.utc).isoformat(), "v": valor},
                   ensure_ascii=False), encoding="utf-8")


def _safe(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower())[:40]


def _get(path: str, params: dict, key: str):
    url = f"{HOST}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"x-apisports-key": key})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def equipo(nombre: str, key: str) -> dict | None:
    """
    Busca id y logo por nombre (cacheado). CLAVE: si el nombre es un país conocido
    (selección), exige que el equipo sea NACIONAL (national=true), para no traer por
    error un club con nombre parecido. Para clubes, evita devolver una selección.
    """
    cn = "team_v3_" + _safe(nombre)
    c = _cache_get(cn)
    if c is not None:
        return c
    try:
        data = _get("/teams", {"search": nombre}, key)
        resp = data.get("response", [])
        if not resp:
            _cache_set(cn, None)
            return None
        es_seleccion = banderas.iso_de(nombre) is not None

        def _variante(n):  # femenina / juvenil / olímpica: NO es la absoluta masculina
            n = (n or "").lower()
            return (n.endswith(" w") or "women" in n or "olympic" in n or "olímpic" in n
                    or any(x in n for x in ("u20", "u-20", "u23", "u-23", "u21", "u-21", "u17", "u-17")))

        elegido = None
        if es_seleccion:
            nac = [r["team"] for r in resp if r["team"].get("national")]
            absoluta = [t for t in nac if not _variante(t["name"])]
            elegido = absoluta[0] if absoluta else (nac[0] if nac else None)
        else:
            for r in resp:  # club: descarta selecciones nacionales
                if not r["team"].get("national"):
                    elegido = r["team"]
                    break
        if elegido is None:
            elegido = resp[0]["team"]
        out = {"id": elegido["id"], "nombre": elegido["name"],
               "logo": elegido.get("logo"), "national": elegido.get("national")}
        _cache_set(cn, out)
        return out
    except Exception:  # noqa: BLE001
        return None


def _resumir_fixture(fx: dict, foco_id: int | None = None) -> dict:
    g = fx["goals"]
    home = fx["teams"]["home"]
    away = fx["teams"]["away"]
    res = {
        "fixture_id": fx["fixture"]["id"],
        "fecha": (fx["fixture"]["date"] or "")[:10],
        "local": home["name"], "visitante": away["name"],
        "logo_local": home.get("logo"), "logo_visitante": away.get("logo"),
        "marcador": f"{g['home']}-{g['away']}" if g["home"] is not None else "-",
    }
    if foco_id is not None and g["home"] is not None:
        es_local = home["id"] == foco_id
        gf, gc = (g["home"], g["away"]) if es_local else (g["away"], g["home"])
        res["resultado"] = "G" if gf > gc else ("E" if gf == gc else "P")
        res["gf"], res["gc"] = gf, gc
    return res


def _resumen_forma(forma_lista: list[dict]) -> dict | None:
    """Promedio de goles a favor/en contra, % de partidos con +2.5 goles y racha."""
    js = [f for f in forma_lista if f.get("gf") is not None]
    if not js:
        return None
    n = len(js)
    return {
        "gf": round(sum(f["gf"] for f in js) / n, 1),
        "gc": round(sum(f["gc"] for f in js) / n, 1),
        "over25": round(sum(1 for f in js if f["gf"] + f["gc"] > 2.5) / n * 100),
        "racha": "".join(f.get("resultado", "") for f in js[:5]),
    }


def _anio_actual() -> int:
    return dt.datetime.now().year


def _jugado(fx: dict) -> bool:
    return (fx["fixture"]["status"]["short"] in ("FT", "AET", "PEN")
            and fx["goals"]["home"] is not None)


def forma(team_id: int, key: str, n: int = 5) -> list[dict]:
    """Últimos n partidos jugados. El plan free no permite 'last', así que pedimos
    por temporada (año actual y, si hace falta, el anterior) y ordenamos."""
    cn = f"forma_{team_id}_{n}_v5"
    c = _cache_get(cn)
    if c is not None:
        return c
    try:
        jugados = []
        tope = min(_anio_actual(), 2024)  # el plan free cubre temporadas 2022-2024
        for season in range(tope, tope - 3, -1):
            data = _get("/fixtures", {"team": team_id, "season": season}, key)
            jugados += [fx for fx in data.get("response", []) if _jugado(fx)]
            if len(jugados) >= n:
                break
        jugados.sort(key=lambda fx: fx["fixture"]["date"], reverse=True)
        out = [_resumir_fixture(fx, team_id) for fx in jugados[:n]]
        _cache_set(cn, out)
        return out
    except Exception:  # noqa: BLE001
        return []


def h2h(id1: int, id2: int, key: str, n: int = 10) -> list[dict]:
    """Historial directo (incluye amistosos). Sin 'last' (no disponible en free)."""
    cn = f"h2h_{min(id1,id2)}_{max(id1,id2)}_{n}_v2"
    c = _cache_get(cn)
    if c is not None:
        return c
    try:
        data = _get("/fixtures/headtohead", {"h2h": f"{id1}-{id2}"}, key)
        jugados = [fx for fx in data.get("response", []) if _jugado(fx)]
        jugados.sort(key=lambda fx: fx["fixture"]["date"], reverse=True)
        out = [_resumir_fixture(fx) for fx in jugados[:n]]
        _cache_set(cn, out)
        return out
    except Exception:  # noqa: BLE001
        return []


def estadisticas_fixture(fixture_id: int, team_id: int, key: str) -> dict:
    """Córners, posesión y tiros de un equipo en un partido concreto (cacheado)."""
    cn = f"stats_{fixture_id}_{team_id}_v2"
    c = _cache_get(cn)
    if c is not None:
        return c
    try:
        data = _get("/fixtures/statistics", {"fixture": fixture_id, "team": team_id}, key)
        resp = data.get("response", [])
        out = {"corners": None, "posesion": None, "tiros": None, "tiros_arco": None, "amarillas": None, "faltas": None}
        if resp:
            for st in resp[0].get("statistics", []):
                t, v = st.get("type"), st.get("value")
                if t == "Corner Kicks":
                    out["corners"] = v
                elif t == "Ball Possession":
                    out["posesion"] = v
                elif t == "Total Shots":
                    out["tiros"] = v
                elif t == "Shots on Goal":
                    out["tiros_arco"] = v
                elif t == "Yellow Cards":
                    out["amarillas"] = v
                elif t == "Fouls":
                    out["faltas"] = v
        _cache_set(cn, out)
        return out
    except Exception:  # noqa: BLE001
        return {}


def alineacion_fixture(fixture_id: int, team_id: int, key: str) -> dict | None:
    """Formación y once de un equipo en un partido concreto (cacheado)."""
    cn = f"lineup_{fixture_id}_{team_id}"
    c = _cache_get(cn)
    if c is not None:
        return c
    try:
        data = _get("/fixtures/lineups", {"fixture": fixture_id, "team": team_id}, key)
        resp = data.get("response", [])
        out = None
        if resp:
            l = resp[0]
            out = {"formacion": l.get("formation"),
                   "once": [p["player"]["name"] for p in l.get("startXI", []) if p.get("player")][:11]}
        _cache_set(cn, out)
        return out
    except Exception:  # noqa: BLE001
        return None


def _previo(forma_lista: list[dict], team_id: int, key: str) -> dict | None:
    """Datos del último partido jugado: rival, marcador, córners y formación."""
    if not forma_lista:
        return None
    ult = forma_lista[0]
    fid = ult.get("fixture_id")
    if not fid:
        return None
    st = estadisticas_fixture(fid, team_id, key)
    al = alineacion_fixture(fid, team_id, key)
    return {
        "fecha": ult["fecha"], "local": ult["local"], "visitante": ult["visitante"],
        "marcador": ult["marcador"], "resultado": ult.get("resultado"),
        "corners": st.get("corners"), "posesion": st.get("posesion"),
        "tiros": st.get("tiros"), "tiros_arco": st.get("tiros_arco"),
        "amarillas": st.get("amarillas"), "faltas": st.get("faltas"),
        "formacion": al.get("formacion") if al else None,
        "once": al.get("once") if al else None,
    }


def tendencia(forma_lista: list[dict], team_id: int, key: str, n: int = 3) -> dict | None:
    """Promedio de córners, tiros y amarillas de los últimos n partidos (reusa caché)."""
    fs = [f for f in forma_lista if f.get("fixture_id")][:n]
    cor, amar, tir = [], [], []
    for f in fs:
        st = estadisticas_fixture(f["fixture_id"], team_id, key)
        if st.get("corners") is not None:
            cor.append(st["corners"])
        if st.get("amarillas") is not None:
            amar.append(st["amarillas"])
        if st.get("tiros") is not None:
            tir.append(st["tiros"])
    prom = lambda l: round(sum(l) / len(l), 1) if l else None  # noqa: E731
    if not (cor or amar or tir):
        return None
    return {"corners": prom(cor), "amarillas": prom(amar), "tiros": prom(tir), "n": len(fs)}


def detalle_partido(local: str, visitante: str, key: str) -> dict:
    """Devuelve {disponible, h2h, forma_local, forma_visitante, logos, resumen_h2h}."""
    if not key:
        return {"disponible": False, "mensaje": "Conecta API-Football (gratis) para H2H, forma y logos."}
    el = equipo(local, key)
    ev = equipo(visitante, key)
    if not el or not ev:
        return {"disponible": False,
                "mensaje": "No se pudieron cargar los datos avanzados (equipo no hallado o "
                           "límite diario de API-Football alcanzado — se renueva cada día)."}
    enf = h2h(el["id"], ev["id"], key)
    # resumen del h2h desde la perspectiva del local
    g = e = p = 0
    for m in enf:
        gh, ga = (m["marcador"].split("-") + ["", ""])[:2]
        if not gh.isdigit():
            continue
        gh, ga = int(gh), int(ga)
        loc_es_home = m["local"] == el["nombre"]
        gf, gc = (gh, ga) if loc_es_home else (ga, gh)
        g += gf > gc; e += gf == gc; p += gf < gc
    fl = forma(el["id"], key)
    fv = forma(ev["id"], key)
    return {
        "disponible": True,
        "logo_local": el["logo"], "logo_visitante": ev["logo"],
        "forma_local": fl,
        "forma_visitante": fv,
        "nota_forma": "Últimos partidos disponibles en el plan gratuito de API-Football (ver fechas).",
        "resumen_local": _resumen_forma(fl),
        "resumen_visitante": _resumen_forma(fv),
        "tendencia_local": tendencia(fl, el["id"], key),
        "tendencia_visitante": tendencia(fv, ev["id"], key),
        "previo_local": _previo(fl, el["id"], key),
        "previo_visitante": _previo(fv, ev["id"], key),
        "h2h": enf,
        "nota_h2h": "Historial del plan gratuito de API-Football (desde ~2013, incluye amistosos).",
        "resumen_h2h": {"local": el["nombre"], "visitante": ev["nombre"],
                        "g": g, "e": e, "p": p, "total": len(enf)},
    }
