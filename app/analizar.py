#!/usr/bin/env python3
"""
analizar.py — Script principal. Genera las mejores apuestas y COMBINADAS para
el horizonte temporal que elijas.

USO BÁSICO (modo demo, sin API key — funciona ya):
    python analizar.py
    python analizar.py --semanas 2
    python analizar.py --dias 10 --patas 3 --perfil conservador

CON DATOS EN VIVO (pon tu API key gratis en .env, ver README.md):
    python analizar.py --fuente odds-api --sport-key soccer_fifa_world_cup --semanas 2

Opciones principales:
    --semanas N      horizonte en semanas (1, 2, 3...). Por defecto 2.
    --dias N         horizonte en días (tiene prioridad sobre --semanas).
    --patas N        nº de selecciones por combinada (2-4 recomendado). Por defecto 3.
    --perfil P       conservador | moderado | agresivo | todos. Por defecto todos.
    --fuente F       demo | odds-api. Por defecto: auto (odds-api si hay key).
    --sport-key K    clave de deporte de The Odds API (ver --listar-deportes).
    --informe        además, guarda un informe .md en ../datos/
    --listar-deportes  imprime los deportes disponibles en The Odds API y sale.
"""
from __future__ import annotations
import argparse
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# En Windows la consola suele ir en cp1252 y rompe con emojis: forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import modelo as M           # noqa: E402
import combinadas as C       # noqa: E402
import datos_demo            # noqa: E402
from clientes import odds_api  # noqa: E402

# Fecha de referencia de los datos DEMO (cuándo se recogieron).
FECHA_DEMO = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
HORIZONTE_FIABLE_DIAS = 14  # más allá de esto las cuotas dejan de ser fiables


# --------------------------------------------------------------------------- #
#  Utilidades
# --------------------------------------------------------------------------- #
def cargar_env() -> dict:
    """Carga variables de ../.env y app/.env sin dependencias externas."""
    env = dict(os.environ)
    for ruta in (Path(__file__).parent / ".env", Path(__file__).parent.parent / ".env"):
        if ruta.exists():
            for linea in ruta.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def filtrar_horizonte(eventos: list[dict], dias: int, base: dt.datetime) -> list[dict]:
    limite = base + dt.timedelta(days=dias)
    out = []
    for ev in eventos:
        f = dt.datetime.fromisoformat(ev["fecha"].replace("Z", "+00:00"))
        if base - dt.timedelta(days=1) <= f <= limite:
            out.append(ev)
    return sorted(out, key=lambda e: e["fecha"])


def aviso_horizonte(dias: int) -> None:
    if dias <= HORIZONTE_FIABLE_DIAS:
        return
    print()
    print("  ⚠️  AVISO DE FIABILIDAD ".center(70, "─"))
    print(f"  Pediste un horizonte de {dias} días. Las casas rara vez publican")
    print(f"  cuotas fiables más allá de ~{HORIZONTE_FIABLE_DIAS} días: no se conocen")
    print("  lesiones, alineaciones ni rivales finales, y las cuotas se mueven mucho.")
    print("  → Los eventos lejanos pueden faltar o tener estimaciones poco precisas.")
    print("  Recomendación: trabaja con horizontes de 7-14 días para máxima precisión.")
    print("─" * 70)


# --------------------------------------------------------------------------- #
#  Impresión
# --------------------------------------------------------------------------- #
def fmt_pct(x: float) -> str:
    return f"{x * 100:5.1f}%"


def imprimir_simples(titulo: str, lista: list[C.ApuestaSimple]) -> None:
    print(f"\n### {titulo}")
    print(f"{'Selección':<42}{'Cuota':>7}{'Prob':>8}{'EV':>8}  {'Perfil'}")
    print("-" * 90)
    for s in lista:
        perfil = M.clasificar_perfil(s.prob_real)
        print(f"{(s.partido + ' — ' + s.descripcion)[:41]:<42}"
              f"{s.cuota:>7.2f}{fmt_pct(s.prob_real):>8}{s.ev:>+8.2f}  {perfil}")


def imprimir_combinadas(perfil: str, combis: list[C.Combinada]) -> None:
    etiqueta = {"conservador": "🟢 CONSERVADORA", "moderado": "🟡 MODERADA",
                "agresivo": "🔴 AGRESIVA"}[perfil]
    print(f"\n╔══ COMBINADA {etiqueta} " + "═" * (50 - len(etiqueta)))
    if not combis:
        print("║  (No hay suficientes eventos fiables en este horizonte para este perfil.)")
        print("╚" + "═" * 60)
        return
    for i, c in enumerate(combis, 1):
        print(f"║")
        print(f"║  Opción {i}:  cuota {c.cuota:.2f}  |  prob. acertar TODO ≈ {fmt_pct(c.prob)}"
              f"  |  EV {c.ev:+.2f}")
        print(f"║  Si apuestas $100 → ganas ${c.ganancia_por_100():.0f} si entra entera")
        for p in c.patas:
            f = p.fecha[:10]
            print(f"║     • [{f}] {p.partido} → {p.descripcion}  @ {p.cuota:.2f} ({fmt_pct(p.prob_real)})")
    print("╚" + "═" * 60)


def escribir_informe(ruta: Path, dias: int, eventos, simples,
                     combis_por_perfil) -> None:
    L = []
    hoy = FECHA_DEMO.strftime("%Y-%m-%d")
    L.append(f"# Informe de apuestas — horizonte {dias} días (gen. {hoy})\n")
    L.append("> Generado automáticamente por la app. Verifica las cuotas antes de apostar.\n")
    L.append(f"\n**Eventos analizados en el periodo:** {len(eventos)}\n")

    L.append("\n## Apuestas individuales más seguras\n")
    L.append("| Selección | Cuota | Prob. real | EV |\n|---|---|---|---|")
    for s in C.mejores_simples(simples, 10):
        L.append(f"| {s.partido} — {s.descripcion} | {s.cuota:.2f} | {fmt_pct(s.prob_real)} | {s.ev:+.2f} |")

    for perfil, combis in combis_por_perfil.items():
        L.append(f"\n## Combinadas — perfil {perfil}\n")
        if not combis:
            L.append("_Sin combinadas válidas en este horizonte._")
            continue
        for i, c in enumerate(combis, 1):
            L.append(f"\n**Opción {i}** — cuota {c.cuota:.2f}, prob. ≈ {fmt_pct(c.prob)}, "
                     f"EV {c.ev:+.2f} (gana ${c.ganancia_por_100():.0f} por $100):")
            for p in c.patas:
                L.append(f"- [{p.fecha[:10]}] {p.partido} → {p.descripcion} @ {p.cuota:.2f}")

    ruta.write_text("\n".join(L), encoding="utf-8")
    print(f"\n📄 Informe guardado en: {ruta}")


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description="Generador de apuestas y combinadas por horizonte.")
    ap.add_argument("--semanas", type=int, default=2)
    ap.add_argument("--dias", type=int, default=None)
    ap.add_argument("--patas", type=int, default=3)
    ap.add_argument("--perfil", choices=["conservador", "moderado", "agresivo", "todos"],
                    default="todos")
    ap.add_argument("--fuente", choices=["demo", "odds-api", "auto"], default="auto")
    ap.add_argument("--sport-key", default="soccer_fifa_world_cup")
    ap.add_argument("--region", default="eu")
    ap.add_argument("--informe", action="store_true")
    ap.add_argument("--listar-deportes", action="store_true")
    args = ap.parse_args()

    env = cargar_env()
    api_key = env.get("ODDS_API_KEY", "").strip()

    if args.listar_deportes:
        if not api_key:
            print("Necesitas ODDS_API_KEY en .env para listar deportes. Ver README.md")
            return
        for d in odds_api.listar_deportes(api_key):
            print(f"  {d['key']:<32} {d.get('title','')}")
        return

    dias = args.dias if args.dias is not None else args.semanas * 7

    # --- elegir fuente de datos ---
    fuente = args.fuente
    if fuente == "auto":
        fuente = "odds-api" if api_key else "demo"

    base = dt.datetime.now(dt.timezone.utc)
    if fuente == "odds-api":
        if not api_key:
            print("⚠️  No hay ODDS_API_KEY en .env → usando modo DEMO.")
            fuente = "demo"
        else:
            try:
                eventos = odds_api.obtener_eventos(api_key, args.sport_key, dias, args.region)
                print(f"✅ Datos en vivo de The Odds API ({args.sport_key}, región {args.region}).")
            except RuntimeError as e:
                print(f"⚠️  {e}\n→ Cayendo a modo DEMO con datos del 10/06/2026.")
                fuente = "demo"

    if fuente == "demo":
        eventos = datos_demo.EVENTOS_DEMO
        base = FECHA_DEMO
        print("ℹ️  Modo DEMO: datos reales recogidos el 10/06/2026 (sin API key).")

    eventos = filtrar_horizonte(eventos, dias, base)

    # --- cabecera ---
    print("\n" + "═" * 70)
    print(f"  ANÁLISIS DE APUESTAS  ·  horizonte: {dias} días "
          f"({dias/7:.1f} semanas)  ·  {len(eventos)} eventos")
    print("═" * 70)
    aviso_horizonte(dias)

    if not eventos:
        print("\nNo hay eventos en este horizonte. Prueba a ampliar --dias o cambiar --sport-key.")
        return

    simples = C.generar_simples(eventos)

    imprimir_simples("APUESTAS INDIVIDUALES MÁS SEGURAS (mayor probabilidad)",
                     C.mejores_simples(simples, 8))
    imprimir_simples("APUESTAS INDIVIDUALES CON MÁS VALOR (mayor EV)",
                     C.mejores_por_valor(simples, 6))

    perfiles = ["conservador", "moderado", "agresivo"] if args.perfil == "todos" else [args.perfil]
    combis_por_perfil = {}
    for perfil in perfiles:
        combis = C.mejores_combinadas(simples, perfil, n_patas=args.patas, top=3)
        combis_por_perfil[perfil] = combis
        imprimir_combinadas(perfil, combis)

    print("\n" + "─" * 70)
    print("  Recordatorio: una combinada de N patas es MENOS probable que cualquiera")
    print("  de sus patas por separado. 'Más segura' = apuesta SIMPLE. Apuesta solo")
    print("  lo que puedas permitirte perder. Ver ../analisis/04-metodologia-gestion-riesgo.md")
    print("─" * 70)

    if args.informe:
        destino = Path(__file__).parent.parent / "datos" / f"informe_{dias}d.md"
        escribir_informe(destino, dias, eventos, simples, combis_por_perfil)


if __name__ == "__main__":
    main()
