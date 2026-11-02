"""
combinadas.py — Motor de generación de apuestas individuales y combinadas.

A partir de los eventos (con cuotas), genera:
  1. Apuestas SIMPLES candidatas (ganador, doble oportunidad, over/under) con
     su probabilidad real (de-vig) y su valor esperado.
  2. Las MEJORES COMBINADAS para un horizonte temporal, optimizadas por perfil:
        - conservador: máxima probabilidad de acertar toda la combinada.
        - moderado:    equilibrio probabilidad / pago.
        - agresivo:    máximo valor esperado (EV).

Regla de oro respetada: nunca se combinan dos apuestas del MISMO partido
(estarían correlacionadas y no es una combinada válida en la mayoría de casas).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from itertools import combinations
import modelo as M


def _cuota_doble(p1: float, p2: float, margen: float = 1.04) -> float:
    """
    Cuota de mercado realista para una doble oportunidad que cubre dos
    resultados con probabilidades reales p1 y p2. Parte de la cuota justa
    1/(p1+p2), le aplica un margen típico de casa (~4%) y nunca baja de 1.01.
    """
    justa = 1.0 / (p1 + p2)
    return max(1.01, round(justa / margen, 3))


@dataclass
class ApuestaSimple:
    evento_id: str
    deporte: str
    partido: str
    fecha: str
    mercado: str          # "Ganador", "Doble oportunidad", "Over/Under"
    descripcion: str      # texto legible de la selección
    cuota: float
    prob_real: float

    @property
    def ev(self) -> float:
        return M.valor_esperado(self.prob_real, self.cuota)


@dataclass
class Combinada:
    patas: list[ApuestaSimple]
    criterio: str = ""
    prob: float = field(init=False)
    cuota: float = field(init=False)
    ev: float = field(init=False)

    def __post_init__(self):
        self.prob = M.prob_combinada([p.prob_real for p in self.patas])
        self.cuota = M.cuota_combinada([p.cuota for p in self.patas])
        self.ev = self.prob * self.cuota - 1  # EV por unidad apostada

    def ganancia_por_100(self) -> float:
        return round((self.cuota - 1) * 100, 2)


# --------------------------------------------------------------------------- #
#  1. Generar apuestas simples desde un evento
# --------------------------------------------------------------------------- #
def _simples_de_evento(ev: dict) -> list[ApuestaSimple]:
    out: list[ApuestaSimple] = []
    partido = f"{ev['local']} vs {ev['visitante']}"
    m = ev["mercados"]

    if "1x2" in m:
        cl = m["1x2"]["local"]
        cv = m["1x2"]["visitante"]
        ce = m["1x2"].get("empate")

        if ce:  # deporte CON empate (fútbol)
            devig = M.devig([cl, ce, cv])
            # Ganador local / visitante
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Ganador", f"{ev['local']} gana", cl, devig[0]))
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Ganador", f"{ev['visitante']} gana", cv, devig[2]))
            # Doble oportunidad (cuota de mercado realista desde las probs de-vig)
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Doble oportunidad",
                                     f"{ev['local']} gana o empata (1X)",
                                     _cuota_doble(devig[0], devig[1]), devig[0] + devig[1]))
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Doble oportunidad",
                                     f"{ev['visitante']} gana o empata (X2)",
                                     _cuota_doble(devig[1], devig[2]), devig[1] + devig[2]))
        else:  # deporte SIN empate (NBA, tenis...)
            devig = M.devig([cl, cv])
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Ganador", f"{ev['local']} gana", cl, devig[0]))
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Ganador", f"{ev['visitante']} gana", cv, devig[1]))

    if "total" in m:
        linea = m["total"]["linea"]
        co, cu = m["total"]["over"], m["total"]["under"]
        dv = M.devig([co, cu])
        out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                 "Over/Under", f"Over {linea} goles", co, dv[0]))
        out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                 "Over/Under", f"Under {linea} goles", cu, dv[1]))
    elif "1x2" in m and m["1x2"].get("empate"):
        # Si no hay mercado de totales pero sí 1X2, derivamos O/U 2.5 con Poisson.
        devig = M.devig([m["1x2"]["local"], m["1x2"]["empate"], m["1x2"]["visitante"]])
        lam = M.lambdas_desde_mercado(*devig, total_esperado=2.6)
        if lam:
            mat = M.matriz_marcadores(lam[0], lam[1])
            p_over = M.prob_over(mat, 2.5)
            cuota_just_over = round(1 / p_over / 1.05, 3) if p_over > 0 else None  # margen 5%
            cuota_just_under = round(1 / (1 - p_over) / 1.05, 3)
            if cuota_just_over:
                out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                         "Over/Under (modelo)", "Over 2.5 goles (estimado)",
                                         cuota_just_over, p_over))
            out.append(ApuestaSimple(ev["id"], ev["deporte"], partido, ev["fecha"],
                                     "Over/Under (modelo)", "Under 2.5 goles (estimado)",
                                     cuota_just_under, 1 - p_over))
    return out


def generar_simples(eventos: list[dict]) -> list[ApuestaSimple]:
    out: list[ApuestaSimple] = []
    for ev in eventos:
        out.extend(_simples_de_evento(ev))
    return out


# --------------------------------------------------------------------------- #
#  2. Construir las mejores combinadas por perfil
# --------------------------------------------------------------------------- #
PERFILES = {
    # nombre: (cuota_min_combinada, prob_min_por_pata, criterio_orden)
    "conservador": dict(cuota_min=1.10, prob_pata_min=0.75, orden="prob"),
    "moderado":    dict(cuota_min=1.40, prob_pata_min=0.58, orden="prob"),
    "agresivo":    dict(cuota_min=1.90, prob_pata_min=0.45, orden="ev"),
}


def mejores_combinadas(simples: list[ApuestaSimple], perfil: str,
                       n_patas: int = 3, top: int = 5) -> list[Combinada]:
    """
    Devuelve las `top` mejores combinadas de `n_patas` para el perfil dado.
    - Considera todas las patas que cumplan la prob. mínima del perfil.
    - NUNCA combina dos patas del mismo evento (estarían correlacionadas).
    - Filtra por cuota mínima (para que la combinada pague algo) y ordena por
      probabilidad (perfiles de seguridad) o por valor esperado (agresivo).
    """
    cfg = PERFILES[perfil]
    candidatas = [s for s in simples if s.prob_real >= cfg["prob_pata_min"]]
    # acotamos para evitar explosión combinatoria, priorizando las más fuertes
    clave = (lambda s: s.ev) if cfg["orden"] == "ev" else (lambda s: s.prob_real)
    candidatas = sorted(candidatas, key=clave, reverse=True)[:24]

    if len(candidatas) < n_patas:
        n_patas = max(1, len(candidatas))

    combis: list[Combinada] = []
    for grupo in combinations(candidatas, n_patas):
        if len({p.evento_id for p in grupo}) < n_patas:
            continue  # descartamos combinadas con dos patas del mismo partido
        c = Combinada(list(grupo), criterio=perfil)
        if c.cuota < cfg["cuota_min"]:
            continue
        combis.append(c)

    if cfg["orden"] == "ev":
        combis.sort(key=lambda c: c.ev, reverse=True)
    else:
        combis.sort(key=lambda c: c.prob, reverse=True)

    return combis[:top]


def mejores_simples(simples: list[ApuestaSimple], top: int = 8) -> list[ApuestaSimple]:
    """Las apuestas individuales más seguras (mayor probabilidad real)."""
    return sorted(simples, key=lambda s: s.prob_real, reverse=True)[:top]


def mejores_por_valor(simples: list[ApuestaSimple], top: int = 8) -> list[ApuestaSimple]:
    """Las apuestas individuales con mayor valor esperado (EV)."""
    return sorted(simples, key=lambda s: s.ev, reverse=True)[:top]
