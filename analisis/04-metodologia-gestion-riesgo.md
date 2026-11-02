# 🧠 Metodología y Gestión de Riesgo

> Esto es lo que separa apostar con criterio de apostar a ciegas. Léelo una vez y lo aplicas siempre.

---

## 1. Convertir cuota → probabilidad (probabilidad implícita)

- **Cuota decimal a probabilidad:** `prob = 1 / cuota`. Ej: cuota 1.42 → 1/1.42 = 70.4%.
- **Cuota americana a decimal:**
  - Negativa (-240): `decimal = 1 + 100/240 = 1.417`
  - Positiva (+350): `decimal = 1 + 350/100 = 4.50`

## 2. Quitar el margen de la casa (de-vig) — la "probabilidad justa"

Las casas inflan las cuotas para garantizarse ganancia. La suma de las probabilidades
implícitas de un partido **supera el 100%**; ese exceso es el **margen (vig/overround)**.

**Ejemplo real — México vs Sudáfrica:**
```
México   1/1.42 = 70.6%
Empate   1/4.40 = 22.7%
Sudáfrica 1/8.50 = 11.8%
SUMA            = 105.1%   ← margen de la casa = 5.1%
```
Para estimar la probabilidad **real**, divides cada una entre la suma:
```
México real   = 70.6 / 105.1 = 67.2%
Empate real   = 22.7 / 105.1 = 21.6%
Sudáfrica real = 11.8 / 105.1 = 11.2%
```
👉 La columna "Prob. real (de-vig)" de los análisis sale de aquí. La app lo hace automático.

## 3. Valor Esperado (EV) — ¿la apuesta vale la pena a largo plazo?

```
EV = prob_real × (cuota − 1) − (1 − prob_real)
```
- **EV > 0** → apuesta con **valor** (ganas a largo plazo si repites muchas veces).
- **EV < 0** → la casa tiene ventaja (pierdes a largo plazo).

**Ejemplo — México gana @ 1.42, prob real 67.2%:**
```
EV = 0.672 × 0.42 − 0.328 = 0.282 − 0.328 = −0.046  →  −4.6%
```
> 🔑 **Lección clave:** incluso un favorito "seguro" suele tener **EV negativo** por el margen.
> Lo "seguro" no es lo mismo que lo "rentable". Apostar a favoritos baratos repetidamente
> **erosiona tu dinero lentamente**. Ganar a largo plazo exige encontrar cuotas donde tu
> estimación de probabilidad supere a la implícita de la casa (EV > 0). Eso es difícil y arriesgado.

## 4. La FALACIA de las combinadas "seguras" (matemática)

Cada selección que añades **multiplica** las probabilidades:
```
Combinada de N eventos: prob_total = p1 × p2 × ... × pN
```
| Combinada | Cálculo | Prob. de acertar TODO |
|-----------|---------|----------------------|
| 1 evento al 85% | 0.85 | **85%** |
| 2 eventos al 85% | 0.85² | **72%** |
| 3 eventos al 85% | 0.85³ | **61%** |
| 4 eventos al 85% | 0.85⁴ | **52%** |
| 6 eventos al 85% | 0.85⁶ | **38%** |

> La casa te muestra una **cuota total alta y atractiva**, pero esa cuota esconde que la
> probabilidad real se ha desplomado. Además, **el margen de la casa se aplica en CADA pata**,
> así que el EV de una combinada es **peor** que el de las apuestas por separado. Por eso las
> casas regalan "boosts" de combinadas: son su producto más rentable.

**Regla práctica:** si buscas seguridad, **apuesta simple**. Si combinas, que sea de 2 patas
máximo y de eventos muy probables (dobles oportunidad). Nunca combines 5-6 "para asegurar".

## 5. Gestión de bankroll (lo que de verdad te protege)

1. **Define un bankroll**: dinero total que destinas a esto y que puedes perder sin afectar tu vida.
2. **Stake fijo conservador:** apuesta **1–3% del bankroll por jugada**. Nunca el 50% a "una segura".
3. **Criterio de Kelly (avanzado):** la fracción óptima a apostar es
   ```
   f = (cuota × prob_real − 1) / (cuota − 1)
   ```
   - Si f ≤ 0 → **no apuestes** (no hay valor).
   - En la práctica usa **medio Kelly o cuarto de Kelly** (f/2 o f/4): reduce la varianza muchísimo.
   - La app calcula esto por ti.
4. **No persigas pérdidas** (no dobles para "recuperar"). Es la vía rápida a la ruina.
5. **Lleva registro** de cada apuesta (la app puede ayudarte). Sin registro no sabes si ganas o pierdes de verdad.

## 6. El modelo de Poisson (cómo predecimos goles / over-under)

Para mercados de goles (Over/Under, ambos marcan, marcador exacto) usamos la **distribución de
Poisson**, estándar en la analítica de fútbol:
```
P(k goles) = (λ^k × e^−λ) / k!
```
donde `λ` (lambda) es el promedio de goles esperado de un equipo. La app estima λ de dos formas:
- **Desde las cuotas** (de-vig del 1X2 + total) → la más práctica y "de mercado".
- **Desde la fuerza ataque/defensa** (estilo Dixon-Coles) si le das medias de goles.

Con la matriz de marcadores Poisson se derivan automáticamente: prob. de Over/Under X.5,
ambos equipos marcan (BTTS), y marcadores exactos. Ver `app/modelo.py`.

---

## ✅ Checklist antes de cada apuesta

- [ ] ¿Calculé la probabilidad real (de-vig), no solo la cuota?
- [ ] ¿El EV es positivo, o al menos acepto conscientemente un EV negativo a cambio de seguridad?
- [ ] ¿Es simple o, como mucho, combinada de 2 patas muy probables?
- [ ] ¿El stake es ≤ 1–3% de mi bankroll?
- [ ] ¿Verifiqué la cuota actual (no la de hace días)?
- [ ] ¿Estoy apostando dinero que puedo permitirme perder?
