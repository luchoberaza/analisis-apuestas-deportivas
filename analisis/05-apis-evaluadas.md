# 🔌 APIs y Herramientas Evaluadas (con criterio, no a ciegas)

> Pediste que **no tomara las APIs sin criterio**, así que verifiqué la reputación de cada una
> (estrellas de GitHub, opiniones de la comunidad en Reddit/foros de desarrolladores, antigüedad
> y mantenimiento). Aquí está el veredicto honesto. Todas tienen **plan gratuito real**.

---

## ✅ RECOMENDADAS (las que usa la app)

### 1. `openfootball/worldcup.json` — ⭐ MEJOR para fixtures del Mundial
- **Qué es:** datos del Mundial 2026 (calendario, grupos, equipos, resultados) en JSON, **dominio público**.
- **Reputación verificada:** **293 ★ / 41 forks** en GitHub. **Sin API key.** Se actualiza
  ~**una vez al día** vía GitHub Actions. Incluye datos de todos los mundiales 1930→2026.
  Varios proyectos reales en producción lo usan.
- **Pros:** gratis total, sin registro, sin límites, open source y auditado.
- **Contras:** no trae cuotas ni estadísticas avanzadas (solo calendario/resultados).
- **Veredicto:** 🟢 **Base ideal para fixtures.** Cero fricción.

### 2. The Odds API (`the-odds-api.com`) — ⭐ MEJOR para cuotas
- **Qué es:** cuotas en tiempo real de **20+ casas**, múltiples deportes, formato JSON.
- **Reputación verificada:** la comunidad de **Reddit la valora bien** por *"fiabilidad y
  precisión, buena infraestructura y documentación completa"*. Considerada la opción de
  referencia para *"desarrolladores hobby y apostadores individuales"* — justo nuestro caso.
- **Plan gratis:** **500 créditos/mes** (≈16 peticiones/día). Suficiente para escanear cuotas a diario.
- **Pros:** datos de cuotas fiables, fácil de integrar, decimal y americano.
- **Contras:** los créditos se agotan rápido si haces *polling* amplio o quieres histórico a escala.
- **Veredicto:** 🟢 **Recomendada para cuotas.** Úsala con criterio (pocas llamadas, dirigidas).

### 3. `football-data.org` — sólida para fixtures/resultados como respaldo
- **Qué es:** ligas top + competiciones internacionales (incluye Mundial), JSON.
- **Reputación verificada:** usada por **miles de desarrolladores**; descrita como *"dev-friendly,
  fiable y gratis para siempre"* en las competiciones principales. Comunidad activa (clientes
  no oficiales en PHP, Python, etc.).
- **Plan gratis:** **10 peticiones/min**, competiciones top gratis para siempre. Requiere registro (email).
- **Contras:** datos *live* limitados; no trae cuotas; free tier ajustado para producción seria.
- **Veredicto:** 🟢 **Buen respaldo** para calendario/resultados si quieres una 2ª fuente.

### 4. API-Football (`api-sports.io`) — la más completa (cuotas + predicciones + stats)
- **Qué es:** **600+ ligas**, fixtures, estadísticas, **cuotas y predicciones propias**,
  head-to-head. Mundial vía `league=1, season=2026`. Potencia muchas webs de live-score.
- **Reputación verificada:** proveedor veterano con buena reputación general (reviews en
  SourceForge/Slashdot, amplia adopción). Datos fiables.
- **Plan gratis:** **100 peticiones/día**. Requiere registro y API key.
- **Contras:** el tope de 100/día **se queda corto en días de mucha actividad** (matchdays).
- **Veredicto:** 🟢 **Recomendada como fuente de stats/predicciones** (opcional en la app).
  Úsala para enriquecer, no para *polling* constante.

---

## 🧮 Modelos de predicción (código open-source revisado)

No "tomé" un repo cualquiera: el enfoque que implementé en `app/modelo.py` es el **estándar
académico y de la comunidad** (distribución de Poisson y ajuste Dixon-Coles), el mismo que usan
estos proyectos bien valorados, escrito **propio y comentado** para que entiendas cada línea:

- `dashee87` — *"Predicting Football Results With Statistical Modelling"* (Poisson y Dixon-Coles):
  el tutorial de referencia citado por toda la comunidad.
- `opisthokonta/goalmodel` — paquete consolidado de modelos de goles.
- `ML-KULeuven/soccer_xg` — modelos de xG (expected goals) de un grupo universitario.
- `enzovillafuerte/FootballPredictor-V2.0` — pipeline Poisson + xG sobre 40+ ligas.

> Implementé la lógica yo mismo (no dependes de un repo de terceros que pueda quedar
> abandonado), pero validé que el método coincide con el consenso de estos proyectos.

---

## ❌ DESCARTADAS / con reservas

| Servicio | Por qué no |
|----------|-----------|
| Sportmonks | Potente (predicciones, xG, Pressure Index) pero el plan Mundial es **de pago** (69-129 €/mes). No cumple "gratis". |
| APIs "350+ casas gratis" tipo oddspapi/odds-api.io | Free tiers muy pequeños (250 req/mes) y reputación menos contrastada. Útiles solo como tercera fuente. |
| Cualquier API sin reseñas ni estrellas | Descartada por principio: sin criterio de comunidad, no la uso. |

---

## 🏁 Stack final elegido para la app

```
Fixtures/calendario  →  openfootball/worldcup.json   (sin key, 293★, gratis total)
Cuotas               →  The Odds API                 (free 500/mes, bien valorada en Reddit)
Stats/predicciones   →  API-Football (opcional)      (free 100/día, veterana y completa)
Respaldo resultados  →  football-data.org (opcional) (free, usada por miles de devs)
Modelo predictivo    →  propio (Poisson/Dixon-Coles) (estándar de la comunidad)
```

Todo gratis. Instrucciones para conseguir las keys (gratis) en `app/README.md`.
