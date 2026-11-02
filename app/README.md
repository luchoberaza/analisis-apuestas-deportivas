# 🤖 App — Generador de Apuestas y Combinadas

Herramienta de línea de comandos que, **cuando tú quieras**, te da las mejores
apuestas individuales y **combinadas** para el horizonte temporal que elijas
(1, 2, 3 semanas… hasta donde los datos sigan siendo fiables).

Funciona **sin instalar nada** (solo Python 3.10+) y **sin API key** en modo demo.
Con una API key gratis, trae cuotas **en vivo**.

---

## ⚡ Inicio rápido (modo demo, sin claves)

```bash
cd app
python analizar.py                       # horizonte por defecto: 2 semanas
python analizar.py --semanas 1           # solo la próxima semana
python analizar.py --dias 10 --patas 3   # 10 días, combinadas de 3 patas
python analizar.py --perfil conservador  # solo el perfil más seguro
python analizar.py --informe             # además guarda un .md en ../datos/
```

En Windows puedes usar `py` en vez de `python` si hace falta.

---

## 🔑 Activar datos EN VIVO (gratis)

1. Entra en **https://the-odds-api.com** → "Get API Key" → registro gratis (500 req/mes).
2. Copia `.env.example` a `.env` y pega tu clave:
   ```
   ODDS_API_KEY=tu_clave_aqui
   ```
3. Ejecuta con la fuente en vivo:
   ```bash
   python analizar.py --fuente odds-api --sport-key soccer_fifa_world_cup --semanas 2
   ```
4. ¿No sabes la clave del deporte? Lístalas:
   ```bash
   python analizar.py --listar-deportes
   ```
   Ejemplos: `soccer_fifa_world_cup`, `basketball_nba`, `baseball_mlb`,
   `soccer_conmebol_copa_libertadores`, `tennis_atp`...

> Si la clave falla o se agotan los créditos, la app **cae sola al modo demo** y te avisa.

---

## 🎛️ Todas las opciones

| Opción | Qué hace | Por defecto |
|--------|----------|-------------|
| `--semanas N` | Horizonte en semanas | 2 |
| `--dias N` | Horizonte en días (manda sobre `--semanas`) | — |
| `--patas N` | Selecciones por combinada (2-4 recomendado) | 3 |
| `--perfil P` | `conservador` / `moderado` / `agresivo` / `todos` | todos |
| `--fuente F` | `demo` / `odds-api` / `auto` | auto |
| `--sport-key K` | Deporte de The Odds API | soccer_fifa_world_cup |
| `--region R` | `eu` / `us` / `uk` / `au` | eu |
| `--informe` | Guarda informe `.md` en `../datos/` | off |
| `--listar-deportes` | Muestra deportes disponibles y sale | — |

---

## 📏 ¿Hasta qué horizonte tiene sentido? (tu pregunta)

- **7-14 días: zona fiable.** Las cuotas existen, son estables y los datos (rivales,
  estado físico) se conocen. **Aquí trabaja la app con máxima precisión.**
- **15-21 días: zona gris.** Muchas casas aún no publican cuotas; las que hay se
  moverán mucho. La app te lo **avisa** y usa estimaciones donde puede.
- **+21 días: poco factible.** Salvo grandes favoritos a largo plazo (campeón de
  torneo), no hay mercado de partido fiable. No se recomienda combinar a este plazo.

Por eso la combinada ideal para "las próximas 2 semanas" se arma con partidos de los
**primeros ~14 días**, que es justo lo que cubre la fase de grupos del Mundial ahora.

---

## 🧩 Cómo funciona por dentro

```
analizar.py        ← CLI: elige horizonte, fuente y perfil; imprime e informa
combinadas.py      ← genera apuestas simples y arma/puntúa las combinadas
modelo.py          ← de-vig, valor esperado (EV), Kelly, Poisson (Over/Under, BTTS)
clientes/odds_api.py ← descarga cuotas en vivo de The Odds API (normalizadas)
datos_demo.py      ← cuotas reales del 10/06/2026 (fallback sin API key)
```

El criterio de cada perfil (probabilidad mínima por pata, cuota mínima, si optimiza
por seguridad o por valor) está en `combinadas.PERFILES` — puedes ajustarlo a tu gusto.

---

## ⚠️ Recordatorio

Esto es una herramienta de análisis estadístico, **no una garantía**. Una combinada de
N patas es siempre menos probable que cualquiera de sus patas sueltas. Lo "más seguro"
es la apuesta **simple**. Apuesta solo lo que puedas permitirte perder.
Lee `../analisis/04-metodologia-gestion-riesgo.md`.
