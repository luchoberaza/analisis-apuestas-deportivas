"""
analisis.py — Convierte eventos+cuotas en:
  • apuestas individuales con probabilidad real (de-vig de Shin) y valor esperado,
  • esas apuestas DIVIDIDAS POR DÍA,
  • las mejores COMBINADAS por perfil (conservador / moderado / agresivo).
"""
from __future__ import annotations
import datetime as dt
from itertools import combinations

import modelo as M
import banderas

DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES_ES = ["", "ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic"]

PERFILES = {
    "conservador": dict(cuota_min=1.10, prob_pata_min=0.75, orden="prob"),
    "moderado":    dict(cuota_min=1.40, prob_pata_min=0.58, orden="prob"),
    "agresivo":    dict(cuota_min=1.90, prob_pata_min=0.45, orden="ev"),
}


def _local(iso: str) -> dt.datetime:
    """Convierte la hora UTC del evento a la hora local del sistema."""
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()


def _id(ev: dict) -> str:
    return f"{ev['local']}|{ev['visitante']}|{ev['fecha'][:10]}"


def _apuesta(ev, mercado, seleccion, cuota, prob):
    e = M.valor_esperado(prob, cuota)
    return {
        "evento_id": _id(ev),
        "partido": f"{ev['local']} vs {ev['visitante']}",
        "local": ev["local"], "visitante": ev["visitante"],
        "fecha": ev["fecha"], "mercado": mercado, "seleccion": seleccion,
        "cuota": round(cuota, 3), "prob": round(prob, 4),
        "ev": round(e, 4), "valor": e > 0.005,
        "kelly": round(M.kelly(prob, cuota), 4),
        "perfil": M.clasificar_perfil(prob),
    }


def apuestas_de_evento(ev: dict) -> list[dict]:
    out = []
    m = ev["mercados"]
    if "1x2" in m:
        cl, cv = m["1x2"]["local"], m["1x2"]["visitante"]
        ce = m["1x2"].get("empate")
        if ce:
            pl, pe, pv = M.devig([cl, ce, cv])
            out.append(_apuesta(ev, "Ganador", f"{ev['local']} gana", cl, pl))
            out.append(_apuesta(ev, "Ganador", f"{ev['visitante']} gana", cv, pv))
            out.append(_apuesta(ev, "Doble oportunidad",
                                f"{ev['local']} gana o empata", M.cuota_doble(pl, pe), pl + pe))
            out.append(_apuesta(ev, "Doble oportunidad",
                                f"{ev['visitante']} gana o empata", M.cuota_doble(pe, pv), pe + pv))
            out.append(_apuesta(ev, "Doble oportunidad",
                                "Cualquiera gana (no empate)", M.cuota_doble(pl, pv), pl + pv))
        else:
            pl, pv = M.devig([cl, cv])
            out.append(_apuesta(ev, "Ganador", f"{ev['local']} gana", cl, pl))
            out.append(_apuesta(ev, "Ganador", f"{ev['visitante']} gana", cv, pv))
    if "total" in m:
        linea = m["total"]["linea"]
        co, cu = m["total"]["over"], m["total"]["under"]
        po, pu = M.devig([co, cu])
        out.append(_apuesta(ev, "Goles", f"Over {linea}", co, po))
        out.append(_apuesta(ev, "Goles", f"Under {linea}", cu, pu))
    elif "1x2" in m and m["1x2"].get("empate"):
        pl, pe, pv = M.devig([m["1x2"]["local"], m["1x2"]["empate"], m["1x2"]["visitante"]])
        lam = M.lambdas_desde_mercado(pl, pe, pv)
        if lam:
            mat = M.matriz_marcadores(*lam)
            po = M.prob_over(mat, 2.5)
            out.append(_apuesta(ev, "Goles (modelo)", "Over 2.5 (estimado)",
                                round(1 / po / 1.05, 3), po))
            out.append(_apuesta(ev, "Goles (modelo)", "Under 2.5 (estimado)",
                                round(1 / (1 - po) / 1.05, 3), 1 - po))
            pb = M.prob_btts(mat)
            out.append(_apuesta(ev, "Ambos marcan (modelo)", "Sí (estimado)",
                                round(1 / pb / 1.05, 3), pb))
    return out


def _confianza(prob_top: float) -> dict:
    """Índice de confianza legible según la probabilidad del resultado favorito."""
    if prob_top >= 0.75:
        return {"nivel": "Muy alta", "valor": round(prob_top, 4), "clase": "alta"}
    if prob_top >= 0.55:
        return {"nivel": "Alta", "valor": round(prob_top, 4), "clase": "media-alta"}
    if prob_top >= 0.42:
        return {"nivel": "Media", "valor": round(prob_top, 4), "clase": "media"}
    return {"nivel": "Pareja", "valor": round(prob_top, 4), "clase": "baja"}


def _sugerencias(out: dict, ev: dict) -> list[dict]:
    """Genera consejos de apuesta legibles a partir del modelo (no son cuotas)."""
    s = []
    conf = out.get("confianza")
    fav = out.get("favorito")
    if conf and fav:
        v = conf["valor"]
        if v >= 0.70 and fav != "Empate":
            s.append({"texto": f"Doble oportunidad de {fav}: muy sólida (~{round(v*100)}%)", "nivel": "alta"})
        elif v >= 0.55 and fav != "Empate":
            s.append({"texto": f"{fav} es favorito; la doble oportunidad baja el riesgo", "nivel": "media"})
        else:
            s.append({"texto": "Partido parejo: el 1X2 es arriesgado, mejor doble oportunidad o pasar", "nivel": "info"})
    if out.get("tiene_goles"):
        o25 = out["over_under"]["2.5"]
        btts = out["btts"]
        cor = out["corners"]["total"]
        if o25 >= 0.60:
            s.append({"texto": f"Tiende a goles: Over 2.5 (~{round(o25*100)}%)", "nivel": "alta" if o25 >= 0.66 else "media"})
        elif o25 <= 0.42:
            s.append({"texto": f"Partido cerrado: Under 2.5 (~{round((1-o25)*100)}%)", "nivel": "alta" if o25 <= 0.35 else "media"})
        if btts >= 0.58:
            s.append({"texto": f"Ambos equipos marcan: probable (~{round(btts*100)}%)", "nivel": "media"})
        elif btts <= 0.35:
            s.append({"texto": f"Difícil que ambos marquen (No ~{round((1-btts)*100)}%)", "nivel": "media"})
        linea = max(6.5, int(cor - 2) + 0.5)
        s.append({"texto": f"Córners: la línea Over {linea} luce accesible (estimado ~{cor})", "nivel": "info"})
        if fav and fav != "Empate" and out.get("xg"):
            dx = abs(out["xg"]["local"] - out["xg"]["visitante"])
            if dx >= 1.3:
                s.append({"texto": f"Hándicap asiático: {fav} -1.5 (se espera ganar por 2+)", "nivel": "media"})
            elif dx >= 0.7:
                s.append({"texto": f"Hándicap asiático: {fav} -1 (ventaja clara)", "nivel": "info"})
        if out.get("marcadores"):
            s.append({"texto": f"Marcador más probable: {out['marcadores'][0]['marcador']}", "nivel": "info"})
    return s


def analisis_evento(ev: dict) -> dict:
    """Bloque de análisis del modelo para un partido (marcadores, O/U, BTTS, córners…)."""
    m = ev["mercados"]
    out = {"tiene_goles": False}
    if "1x2" not in m:
        return out
    cl, cv = m["1x2"]["local"], m["1x2"]["visitante"]
    ce = m["1x2"].get("empate")

    if ce:
        pl, pe, pv = M.devig([cl, ce, cv])
        out["probabilidades"] = {"local": round(pl, 4), "empate": round(pe, 4), "visitante": round(pv, 4)}
        top = max([("local", pl), ("empate", pe), ("visitante", pv)], key=lambda t: t[1])
        out["favorito"] = ev["local"] if top[0] == "local" else (ev["visitante"] if top[0] == "visitante" else "Empate")
        out["confianza"] = _confianza(top[1])
        lam = M.lambdas_desde_mercado(pl, pe, pv)
        if lam:
            mat = M.matriz_marcadores(*lam)
            out.update({
                "tiene_goles": True,
                "xg": {"local": round(lam[0], 2), "visitante": round(lam[1], 2),
                       "total": round(lam[0] + lam[1], 2)},
                "marcadores": M.marcadores_top(mat, 5),
                "over_under": {
                    "1.5": round(M.prob_over(mat, 1.5), 4),
                    "2.5": round(M.prob_over(mat, 2.5), 4),
                    "3.5": round(M.prob_over(mat, 3.5), 4),
                },
                "btts": round(M.prob_btts(mat), 4),
                "corners": M.corners_estimados(*lam),
            })
    else:
        pl, pv = M.devig([cl, cv])
        out["probabilidades"] = {"local": round(pl, 4), "visitante": round(pv, 4)}
        top = max([("local", pl), ("visitante", pv)], key=lambda t: t[1])
        out["favorito"] = ev["local"] if top[0] == "local" else ev["visitante"]
        out["confianza"] = _confianza(top[1])
    out["sugerencias"] = _sugerencias(out, ev)
    return out


def dividir_por_dia(eventos: list[dict]) -> list[dict]:
    """Agrupa los eventos por día (hora local) con sus apuestas y análisis."""
    dias: dict[str, dict] = {}
    for ev in sorted(eventos, key=lambda e: e["fecha"]):
        l = _local(ev["fecha"])
        clave = l.strftime("%Y-%m-%d")
        if clave not in dias:
            dias[clave] = {
                "fecha": clave,
                "titulo": f"{DIAS_ES[l.weekday()]} {l.day} {MESES_ES[l.month]}",
                "dia_corto": f"{DIAS_ES[l.weekday()][:3]}", "num": l.day,
                "mes": MESES_ES[l.month], "eventos": [],
            }
        ap = apuestas_de_evento(ev)
        ap_orden = sorted(ap, key=lambda a: a["prob"], reverse=True)
        dias[clave]["eventos"].append({
            "id": _id(ev),
            "partido": f"{ev['local']} vs {ev['visitante']}",
            "torneo": ev.get("categoria_nombre"),
            "categoria_clave": ev.get("categoria_clave"),
            "local": ev["local"], "visitante": ev["visitante"],
            "local_flag": banderas.flag_url(ev["local"]),
            "visitante_flag": banderas.flag_url(ev["visitante"]),
            "hora": l.strftime("%H:%M"),
            "apuestas": ap_orden,
            "modelo": analisis_evento(ev),
        })
    return list(dias.values())


def mejores_combinadas(apuestas: list[dict], perfil: str,
                       n_patas: int = 3, top: int = 4) -> list[dict]:
    cfg = PERFILES[perfil]
    clave = (lambda a: a["ev"]) if cfg["orden"] == "ev" else (lambda a: a["prob"])
    cand = sorted([a for a in apuestas if a["prob"] >= cfg["prob_pata_min"]],
                  key=clave, reverse=True)[:24]
    if len(cand) < n_patas:
        n_patas = max(1, len(cand))
    out = []
    for grupo in combinations(cand, n_patas):
        if len({a["evento_id"] for a in grupo}) < n_patas:
            continue
        prob = M.prob_combinada([a["prob"] for a in grupo])
        cuota = M.cuota_combinada([a["cuota"] for a in grupo])
        if cuota < cfg["cuota_min"]:
            continue
        out.append({
            "patas": list(grupo), "cuota": round(cuota, 2),
            "prob": round(prob, 4), "ev": round(prob * cuota - 1, 4),
            "ganancia_100": round((cuota - 1) * 100, 0),
        })
    out.sort(key=(lambda c: c["ev"]) if cfg["orden"] == "ev" else (lambda c: c["prob"]),
             reverse=True)
    return out[:top]


def analizar(eventos: list[dict], dias: int, patas: int = 3) -> dict:
    """Divide por día (TODO el registro disponible) y arma combinadas (según horizonte)."""
    base = dt.datetime.now(dt.timezone.utc)

    def fecha(e):
        return dt.datetime.fromisoformat(e["fecha"].replace("Z", "+00:00"))

    # Todos los eventos futuros → vista por día + calendario (máximo disponible)
    futuros = [e for e in eventos if fecha(e) >= base - dt.timedelta(days=1)]
    por_dia = dividir_por_dia(futuros)
    calendario = [{"fecha": d["fecha"], "dia_corto": d["dia_corto"], "num": d["num"],
                   "mes": d["mes"], "titulo": d["titulo"], "count": len(d["eventos"])}
                  for d in por_dia]

    # Para combinadas y rankings → solo dentro del horizonte elegido
    limite = base + dt.timedelta(days=dias)
    en_horizonte = [e for e in futuros if fecha(e) <= limite]
    todas = []
    for ev in en_horizonte:
        todas.extend(apuestas_de_evento(ev))
    simples = sorted(todas, key=lambda a: a["prob"], reverse=True)[:10]
    valor = sorted(todas, key=lambda a: a["ev"], reverse=True)[:8]
    combinadas = {p: mejores_combinadas(todas, p, n_patas=patas) for p in PERFILES}

    # --- KPIs de resumen ---
    todos_ev = [e for d in por_dia for e in d["eventos"]]
    def _cval(e):
        return ((e.get("modelo") or {}).get("confianza") or {}).get("valor", 0)
    top = max(todos_ev, key=_cval, default=None)
    kpis = {
        "partidos": len(futuros),
        "partidos_seguros": sum(1 for e in todos_ev if _cval(e) >= 0.75),
        "con_valor": sum(1 for a in todas if a["ev"] > 0),
        "mejor_combi": (combinadas["conservador"][0]["prob"] if combinadas["conservador"] else None),
        "top_confianza": ({"partido": top["partido"], "valor": _cval(top)}
                          if top and _cval(top) > 0 else None),
    }

    return {
        "n_eventos": len(futuros),
        "n_horizonte": len(en_horizonte),
        "dias_disponibles": len(calendario),
        "calendario": calendario,
        "por_dia": por_dia,
        "kpis": kpis,
        "mejores_simples": simples,
        "mejores_valor": valor,
        "combinadas": combinadas,
    }
