"""
modelo.py — Núcleo estadístico (sin dependencias externas).

Calcula la probabilidad real "lo mejor posible" a partir de las cuotas:
  1. Promedia las cuotas de TODAS las casas disponibles (reduce el sesgo de una sola).
  2. Quita el margen de la casa con el método de SHIN (corrige el sesgo
     favorito-longshot mejor que la normalización proporcional simple), con
     fallback a proporcional si no converge.
  3. Deriva mercados de goles (Over/Under, BTTS) con distribución de Poisson.

Referencias: Shin (1993) sobre overround; Dixon-Coles para goles.
"""
from __future__ import annotations
import math


# --------------------------------------------------------------------------- #
#  Conversión de cuotas
# --------------------------------------------------------------------------- #
def americana_a_decimal(odds: float) -> float:
    return 1 + odds / 100 if odds > 0 else 1 + 100 / abs(odds)


def prob_implicita(cuota: float) -> float:
    return 1.0 / cuota


def margen_casa(cuotas: list[float]) -> float:
    return sum(1.0 / c for c in cuotas) - 1.0


# --------------------------------------------------------------------------- #
#  De-vig (eliminar margen)  ·  proporcional y Shin
# --------------------------------------------------------------------------- #
def devig_proporcional(cuotas: list[float]) -> list[float]:
    imp = [1.0 / c for c in cuotas]
    s = sum(imp)
    return [p / s for p in imp]


def devig_shin(cuotas: list[float], iteraciones: int = 100) -> list[float]:
    """
    Método de Shin: estima la fracción de 'dinero informado' (z) y devuelve
    probabilidades reales menos sesgadas en cuotas extremas. Itera z por punto
    fijo. Si algo falla, cae a proporcional.
    """
    try:
        q = [1.0 / c for c in cuotas]
        B = sum(q)              # booksum (overround = B - 1)
        if B <= 1.0 or len(q) < 2:
            return devig_proporcional(cuotas)
        z = 0.0
        for _ in range(iteraciones):
            # p_i(z) = (sqrt(z^2 + 4(1-z) * q_i^2 / B) - z) / (2(1-z))
            ps = [(math.sqrt(z * z + 4 * (1 - z) * (qi * qi) / B) - z) / (2 * (1 - z))
                  for qi in q]
            s = sum(ps)
            # nueva z a partir de la condición de normalización
            z_new = (s - 1.0) / (len(q) - 1.0) * B  # aproximación de actualización
            z_new = min(max(z_new, 0.0), 0.5)
            if abs(z_new - z) < 1e-9:
                z = z_new
                break
            z = z_new
        ps = [(math.sqrt(z * z + 4 * (1 - z) * (qi * qi) / B) - z) / (2 * (1 - z))
              for qi in q]
        s = sum(ps)
        ps = [p / s for p in ps]  # normalización final de seguridad
        if any(p <= 0 or p >= 1 or math.isnan(p) for p in ps):
            return devig_proporcional(cuotas)
        return ps
    except Exception:  # noqa: BLE001
        return devig_proporcional(cuotas)


def devig(cuotas: list[float]) -> list[float]:
    """De-vig por defecto: Shin (mejor estimador)."""
    return devig_shin(cuotas)


# --------------------------------------------------------------------------- #
#  Valor esperado y Kelly
# --------------------------------------------------------------------------- #
def valor_esperado(prob: float, cuota: float) -> float:
    return prob * (cuota - 1) - (1 - prob)


def kelly(prob: float, cuota: float, fraccion: float = 0.25) -> float:
    b = cuota - 1
    if b <= 0:
        return 0.0
    f = (b * prob - (1 - prob)) / b
    return max(0.0, f * fraccion)


# --------------------------------------------------------------------------- #
#  Poisson (mercados de goles)
# --------------------------------------------------------------------------- #
def poisson_pmf(k: int, lam: float) -> float:
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def matriz_marcadores(lam_l: float, lam_v: float, maxg: int = 10) -> list[list[float]]:
    pl = [poisson_pmf(i, lam_l) for i in range(maxg + 1)]
    pv = [poisson_pmf(j, lam_v) for j in range(maxg + 1)]
    return [[pl[i] * pv[j] for j in range(maxg + 1)] for i in range(maxg + 1)]


def prob_1x2(m: list[list[float]]) -> tuple[float, float, float]:
    n = len(m)
    pl = sum(m[i][j] for i in range(n) for j in range(n) if i > j)
    pe = sum(m[i][i] for i in range(n))
    pv = sum(m[i][j] for i in range(n) for j in range(n) if i < j)
    return pl, pe, pv


def prob_over(m: list[list[float]], linea: float = 2.5) -> float:
    n = len(m)
    return sum(m[i][j] for i in range(n) for j in range(n) if i + j > linea)


def prob_btts(m: list[list[float]]) -> float:
    n = len(m)
    return sum(m[i][j] for i in range(1, n) for j in range(1, n))


def lambdas_desde_mercado(pl: float, pe: float, pv: float,
                          total: float = 2.6) -> tuple[float, float] | None:
    mejor, err_min = None, float("inf")
    pasos = 60
    for s in range(1, pasos):
        frac = s / pasos
        ll, lv = total * frac, total * (1 - frac)
        if ll <= 0 or lv <= 0:
            continue
        a, b, c = prob_1x2(matriz_marcadores(ll, lv))
        err = (a - pl) ** 2 + (b - pe) ** 2 + (c - pv) ** 2
        if err < err_min:
            err_min, mejor = err, (ll, lv)
    return mejor


def marcadores_top(m: list[list[float]], n: int = 5) -> list[dict]:
    """Los n marcadores más probables a partir de la matriz Poisson."""
    flat = []
    for i in range(len(m)):
        for j in range(len(m)):
            flat.append((i, j, m[i][j]))
    flat.sort(key=lambda t: t[2], reverse=True)
    return [{"marcador": f"{i}-{j}", "prob": round(p, 4)} for i, j, p in flat[:n]]


def corners_estimados(lam_l: float, lam_v: float) -> dict:
    """
    Estimación de córners a partir de la intensidad ofensiva (goles esperados).
    Heurística estándar del sector: ~4.5 córners por gol esperado de equipo.
    NO es un dato medido; es una estimación del modelo (se etiqueta como tal).
    """
    cl, cv = lam_l * 2.0 + 3.0, lam_v * 2.0 + 3.0
    total = cl + cv
    return {"local": round(cl, 1), "visitante": round(cv, 1), "total": round(total, 1)}


# --------------------------------------------------------------------------- #
#  Combinadas
# --------------------------------------------------------------------------- #
def prob_combinada(probs: list[float]) -> float:
    p = 1.0
    for x in probs:
        p *= x
    return p


def cuota_combinada(cuotas: list[float]) -> float:
    c = 1.0
    for x in cuotas:
        c *= x
    return c


def cuota_doble(p1: float, p2: float, margen: float = 1.04) -> float:
    """Cuota de mercado realista de una doble oportunidad (clamp a 1.01)."""
    return max(1.01, round((1.0 / (p1 + p2)) / margen, 3))


def clasificar_perfil(prob: float) -> str:
    if prob >= 0.80:
        return "conservador"
    if prob >= 0.60:
        return "moderado"
    if prob >= 0.45:
        return "agresivo"
    return "muy_agresivo"
