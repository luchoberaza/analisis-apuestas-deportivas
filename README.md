# 📊 Análisis de Apuestas Deportivas

Dashboard web que calcula **las mejores apuestas y combinadas** por deporte/competición,
**divididas por día**, con la **probabilidad real** de cada una. Arranca con un comando.

![stack](https://img.shields.io/badge/backend-Flask-blue) ![stack](https://img.shields.io/badge/frontend-React%20%2B%20Tailwind-38bdf8) ![cost](https://img.shields.io/badge/coste-gratis-success)

---

## ⚠️ Léeme primero (30 segundos)

1. **No existe la apuesta 100% segura.** Esto es análisis estadístico, no una garantía. Apuesta solo lo que puedas permitirte perder. +18.
2. **Las combinadas NO son más seguras** — son lo contrario. 4 apuestas del 85% combinadas = 52% de acertar todo. La app te muestra ese número real para que lo veas.
3. La probabilidad se calcula con el **método más preciso que existe**: las cuotas del mercado sin el margen de la casa (de-vig de Shin). Ver `analisis/04-metodologia-gestion-riesgo.md`.

---

## 🚀 Cómo arrancar

```powershell
# 1) Instalar Flask (solo la primera vez)
pip install -r server/requirements.txt

# 2) Arrancar
python server/app.py

# 3) Abrir en el navegador
#    http://localhost:5000
```

Sin configurar nada funciona en **modo demo** (datos reales del 10/06/2026 del Mundial + NBA).

---

## 🔑 Activar datos EN VIVO (gratis)

1. Entra en **https://the-odds-api.com** → "Get API Key" → registro gratis (solo email, **sin tarjeta**).
2. Copia `.env.example` a `.env` y pega tu clave:
   ```
   ODDS_API_KEY=tu_clave_aqui
   ```
3. Reinicia `python server/app.py`. Ahora trae cuotas reales de todas las categorías.

### 💳 ¿Y el límite gratuito? (importante)
- El plan gratis da **500 créditos/mes**. Cada actualización gasta ~2 créditos.
- La app tiene **caché**: solo llama a la API **cada 8 horas** o cuando pulsas **"Actualizar"**.
  Así, actualizando 2 veces al día gastas ~120/mes → **te sobran ~380**.
- Arriba a la derecha ves **cuántos créditos te quedan** en todo momento.
- Si se agotan, **no te cobran nada**: la app sigue mostrando los últimos datos guardados.
- Ajusta el ahorro con `CACHE_TTL_HORAS` en `.env` (súbelo para gastar menos).

---

## 🎛️ Qué hace el dashboard

- **Categorías reales:** Mundial, Libertadores, Champions, Sudamericana, y ligas con su nombre
  (LaLiga, Premier, Serie A, Bundesliga, Ligue 1, Brasileirão, Argentina, Liga MX, MLS),
  más NBA, MLB, NFL y tenis.
- **Horizonte ajustable:** 1, 2, 3 o 4 semanas (con aviso cuando pides un plazo poco fiable >14 días).
- **Pestaña "Por día":** cada partido con sus mejores apuestas, % de probabilidad y barra visual.
- **Pestaña "Combinadas":** las mejores de 2/3/4 patas en 3 perfiles (conservador/moderado/agresivo).
- **Pestaña "Mejor valor":** las apuestas con mayor valor esperado (EV).
- **Recomendación destacada:** la apuesta simple más segura del periodo, arriba del todo.
- Toggle para **mostrar/ocultar cuotas**.

---

## 🗂️ Estructura

```
Analisis-Apuestas-Deportivas/
├── server/                  ← BACKEND (Flask)
│   ├── app.py               · servidor: API + sirve el dashboard
│   ├── modelo.py            · de-vig (Shin), valor esperado, Kelly, Poisson
│   ├── analisis.py          · apuestas por día + combinadas por perfil
│   ├── categorias.py        · subcategorías → claves de The Odds API
│   ├── proveedores.py       · datos con CACHÉ y contador de créditos
│   ├── datos_demo.py        · respaldo sin API key
│   ├── requirements.txt     · Flask
│   └── .env (lo creas tú)
├── web/
│   └── index.html           ← FRONTEND (React + Tailwind, dark)
├── datos/cache/             ← caché automático (no tocar)
├── analisis/                ← documentos de referencia y metodología
└── app/                     ← versión de LÍNEA DE COMANDOS (alternativa, ver app/README.md)
```

---

## 🧪 Estado

Verificado de punta a punta: API (`/api/analizar`, `/api/categorias`), división por día,
combinadas por perfil, caché, casos límite (ligas en pausa, horizonte largo) y compilación del
frontend. Diseño guiado por la skill **ui-ux-pro-max** (estilo data-dense dark) e inspiración de **21st.dev**.
