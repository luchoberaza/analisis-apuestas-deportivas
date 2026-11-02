"""
modelo.py — Núcleo estadístico para análisis de apuestas.

Sin dependencias externas (solo la librería estándar de Python).
Implementa: conversión de cuotas, eliminación del margen de la casa (de-vig),
valor esperado (EV), criterio de Kelly y el modelo de Poisson para goles.

Todo el método sigue el consenso de la comunidad (Poisson / Dixon-Coles).
Ver: analisis/04-metodologia-gestion-riesgo.md
"""
from __future__ import annotations
import math
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
#  1. Conversión de cuotas
# --------------------------------------------------------------------------- #
def americana_a_decimal(odds_americana: float) -> float:
    """Convierte cuota americana (-240, +350) a decimal (1.417, 4.50)."""
    if odds_americana > 0:
        return 1 + odds_americana / 100
    return 1 + 100 / abs(odds_americana)


def prob_implicita(cuota_decimal: float) -> float:
    """Probabilidad implícita (incluye el margen de la casa)."""
    return 1.0 / cuota_decimal


def devig(cuotas_decimales: list[float]) -> list[float]:
    """
    Quita el margen de la casa de un mercado y devuelve las probabilidades
    'justas' normalizadas (suman 1.0). Método de normalización proporcional.
    """
    implicitas = [prob_implicita(c) for c in cuotas_decimales]
    suma = sum(implicitas)
    return [p / suma for p in implicitas]


def margen_casa(cuotas_decimales: list[float]) -> float:
    """Devuelve el overround/margen (ej. 0.051 = 5.1%)."""
    return sum(prob_implicita(c) for c in cuotas_decimales) - 1.0


# --------------------------------------------------------------------------- #
#  2. Valor esperado y Kelly
# --------------------------------------------------------------------------- #
def valor_esperado(prob_real: float, cuota_decimal: float) -> float:
    """
    EV por unidad apostada. Positivo = apuesta con valor a largo plazo.
    EV = p*(cuota-1) - (1-p)
    """
    return prob_real * (cuota_decimal - 1) - (1 - prob_real)


def kelly(prob_real: float, cuota_decimal: float, fraccion: float = 0.25) -> float:
    """
    Fracción del bankroll a apostar según Kelly. Por defecto 'cuarto de Kelly'
    (fraccion=0.25) para reducir varianza. Devuelve 0 si no hay valor.
    """
    b = cuota_decimal - 1
    f = (b * prob_real - (1 - prob_real)) / b
    return max(0.0, f * fraccion)


# --------------------------------------------------------------------------- #
#  3. Modelo de Poisson para goles
# --------------------------------------------------------------------------- #
def poisson_pmf(k: int, lam: float) -> float:
    """Probabilidad de exactamente k eventos dado promedio lam."""
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def matriz_marcadores(lam_local: float, lam_visitante: float,
                      max_goles: int = 10) -> list[list[float]]:
    """
    Matriz de probabilidades de marcador [goles_local][goles_visitante],
    asumiendo independencia (Poisson simple).
    """
    pl = [poisson_pmf(i, lam_local) for i in range(max_goles + 1)]
    pv = [poisson_pmf(j, lam_visitante) for j in range(max_goles + 1)]
    return [[pl[i] * pv[j] for j in range(max_goles + 1)] for i in range(max_goles + 1)]


def prob_1x2(matriz: list[list[float]]) -> tuple[float, float, float]:
    """Devuelve (P_local, P_empate, P_visitante) a partir de la matriz."""
    n = len(matriz)
    p_local = sum(matriz[i][j] for i in range(n) for j in range(n) if i > j)
    p_empate = sum(matriz[i][i] for i in range(n))
    p_visitante = sum(matriz[i][j] for i in range(n) for j in range(n) if i < j)
    return p_local, p_empate, p_visitante


def prob_over(matriz: list[list[float]], linea: float = 2.5) -> float:
    """Probabilidad de Over <linea> goles totales."""
    n = len(matriz)
    return sum(matriz[i][j] for i in range(n) for j in range(n) if i + j > linea)


def prob_under(matriz: list[list[float]], linea: float = 2.5) -> float:
    return 1.0 - prob_over(matriz, linea)


def prob_btts(matriz: list[list[float]]) -> float:
    """Probabilidad de que ambos equipos marquen (BTTS = sí)."""
    n = len(matriz)
    return sum(matriz[i][j] for i in range(1, n) for j in range(1, n))


def lambdas_desde_mercado(p_local: float, p_empate: float, p_visitante: float,
                         total_esperado: float = 2.6) -> tuple[float, float]:
    """
    Estima (lam_local, lam_visitante) que reproducen las probabilidades 1X2
    de-vig del mercado, fijando un total de goles esperado. Búsqueda en rejilla.

    Es el puente entre 'lo que dice el mercado' y 'predicción de marcadores':
    permite derivar Over/Under, BTTS y marcador exacto desde las cuotas 1X2.
    """
    mejor = None
    mejor_error = float("inf")
    # repartimos el total esperado entre local y visitante en muchas proporciones
    pasos = 60
    for s in range(1, pasos):
        frac = s / pasos
        lam_l = total_esperado * frac
        lam_v = total_esperado * (1 - frac)
        if lam_l <= 0 or lam_v <= 0:
            continue
        m = matriz_marcadores(lam_l, lam_v, max_goles=10)
        pl, pe, pv = prob_1x2(m)
        # error cuadrático respecto al 1X2 objetivo
        err = (pl - p_local) ** 2 + (pe - p_empate) ** 2 + (pv - p_visitante) ** 2
        if err < mejor_error:
            mejor_error = err
            mejor = (lam_l, lam_v)
    return mejor


# --------------------------------------------------------------------------- #
#  4. Clasificación de riesgo (etiqueta legible)
# --------------------------------------------------------------------------- #
@dataclass
class Recomendacion:
    descripcion: str
    cuota: float
    prob_real: float
    ev: float
    kelly_frac: float
    perfil: str

    def ganancia_por_100(self) -> float:
        return round((self.cuota - 1) * 100, 2)


def clasificar_perfil(prob_real: float) -> str:
    """Etiqueta de perfil según probabilidad real de acierto."""
    if prob_real >= 0.80:
        return "🟢 Conservador"
    if prob_real >= 0.60:
        return "🟡 Moderado"
    if prob_real >= 0.45:
        return "🔴 Agresivo"
    return "🔴🔴 Muy agresivo"


def analizar_apuesta(descripcion: str, cuota: float, prob_real: float) -> Recomendacion:
    """Construye una recomendación completa para una apuesta individual."""
    return Recomendacion(
        descripcion=descripcion,
        cuota=round(cuota, 3),
        prob_real=round(prob_real, 4),
        ev=round(valor_esperado(prob_real, cuota), 4),
        kelly_frac=round(kelly(prob_real, cuota), 4),
        perfil=clasificar_perfil(prob_real),
    )


def prob_combinada(probs: list[float]) -> float:
    """Probabilidad real de acertar TODAS las patas de una combinada."""
    p = 1.0
    for x in probs:
        p *= x
    return p


def cuota_combinada(cuotas: list[float]) -> float:
    """Cuota total de una combinada (producto de cuotas)."""
    c = 1.0
    for x in cuotas:
        c *= x
    return c
