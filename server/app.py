"""
app.py — Servidor Flask. Expone la API de análisis y sirve el dashboard web.

Arranque:
    cd server
    pip install -r requirements.txt        (solo la primera vez)
    python app.py
    → abre http://localhost:5000

Sin API key funciona en modo DEMO. Con tu key (gratis) en ../.env o server/.env,
trae cuotas en vivo. Ver README.md.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

try:  # consola Windows en cp1252 rompe con acentos/símbolos
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from flask import Flask, jsonify, request, send_from_directory

import categorias
import proveedores
import analisis
import apifootball

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web"

HORIZONTE_FIABLE = 14  # días


def cargar_env() -> dict:
    env = dict(os.environ)
    for ruta in (Path(__file__).parent / ".env", RAIZ / ".env"):
        if ruta.exists():
            for linea in ruta.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    k, v = linea.split("=", 1)
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


ENV = cargar_env()
app = Flask(__name__, static_folder=str(WEB), static_url_path="")
app.json.ensure_ascii = False  # JSON con acentos legibles (UTF-8)


@app.route("/")
def index():
    return send_from_directory(str(WEB), "index.html")


@app.route("/api/categorias")
def api_categorias():
    return jsonify({"grupos": categorias.listar_para_ui()})


@app.route("/api/analizar")
def api_analizar():
    categoria = request.args.get("categoria", "mundial")
    dias = max(1, min(int(request.args.get("dias", 14)), 60))
    patas = max(2, min(int(request.args.get("patas", 3)), 5))
    region = request.args.get("region", "eu")
    forzar = request.args.get("forzar", "0") in ("1", "true", "yes")
    ttl = float(ENV.get("CACHE_TTL_HORAS", 8))

    datos = proveedores.obtener(categoria, ENV, region=region,
                                ttl_horas=ttl, forzar=forzar)
    resultado = analisis.analizar(datos["eventos"], dias=dias, patas=patas)

    aviso = None
    if dias > HORIZONTE_FIABLE:
        aviso = (f"Pediste {dias} días. Las casas rara vez publican cuotas fiables "
                 f"más allá de ~{HORIZONTE_FIABLE} días; los eventos lejanos pueden "
                 f"faltar o ser imprecisos. Recomendado: 7-14 días.")

    return jsonify({
        "categoria": categoria,
        "dias": dias, "patas": patas,
        "meta": datos["meta"],
        "aviso_horizonte": aviso,
        **resultado,
    })


@app.route("/api/partido")
def api_partido():
    """Detalle de UN partido (lazy): modelo + H2H + forma (API-Football si hay key)."""
    categoria = request.args.get("categoria", "mundial")
    local = request.args.get("local", "")
    visitante = request.args.get("visitante", "")
    # Usa el caché de cuotas (ttl alto) para NO gastar créditos de The Odds API aquí.
    datos = proveedores.obtener(categoria, ENV, ttl_horas=10_000, forzar=False)
    ev = next((e for e in datos["eventos"]
               if e["local"] == local and e["visitante"] == visitante), None)
    if not ev:
        return jsonify({"error": "Partido no encontrado"}), 404
    af_key = (ENV.get("APIFOOTBALL_KEY") or "").strip()
    return jsonify({
        "partido": f"{local} vs {visitante}",
        "modelo": analisis.analisis_evento(ev),
        "apuestas": analisis.apuestas_de_evento(ev),
        "avanzado": apifootball.detalle_partido(local, visitante, af_key),
    })


@app.route("/api/deportes")
def api_deportes():
    """Lista las claves de deporte disponibles en vivo (necesita API key)."""
    key = (ENV.get("ODDS_API_KEY") or "").strip()
    if not key:
        return jsonify({"error": "Falta ODDS_API_KEY"}), 400
    import urllib.request
    import json
    url = f"https://api.the-odds-api.com/v4/sports/?apiKey={key}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return jsonify(json.loads(r.read().decode("utf-8")))
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    print("=" * 60)
    print("  Dashboard de Apuestas  ->  http://localhost:5000")
    print("  Modo:", "EN VIVO (API key detectada)" if (ENV.get('ODDS_API_KEY') or '').strip()
          else "DEMO (sin API key - ver README para activar datos en vivo)")
    print("=" * 60)
    app.run(host="127.0.0.1", port=5000, debug=False)
