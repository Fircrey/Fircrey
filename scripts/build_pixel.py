"""Banner en pixel art: Bogotá de noche y el personaje recorriendo los 4 pasos.

Historia (un ciclo):
  camina → 01 Entender (piensa, se enciende la bombilla) → 02 Diseñar (plano)
  → 03 Construir (se sienta a programar) → 04 Desplegar (salta de alegría y
  despega el cohete) → vuelve a empezar.

El fondo va incrustado como PNG nativo escalado con image-rendering: pixelated;
el personaje y el cohete son trazos SVG (nítidos en cualquier pantalla).
Recursos en assets/pixel/ (scripts/tools/make_pixel_assets.py). Requiere Pillow.
"""

from __future__ import annotations

from pathlib import Path

import build_assets as ba
import pixel as px
import sprites as sp

PIX = Path(__file__).resolve().parent.parent / "assets" / "pixel"
S = 3                 # píxeles de pantalla por píxel nativo
GROUND = 145          # fila nativa del suelo
SPEED = 130           # px/s caminando
FLAME = [
    [".....ryyr.....", ".....ryyr.....", "......yy......", "......rr......", ".......r......"],
    ["....ryyyyr....", ".....ryyr.....", ".....ryyr.....", "......yy......", "......r......."],
]


def frames(prefix: str) -> list[px.Grid]:
    return [px.from_png(p) for p in sorted((PIX / "hero").glob(f"{prefix}*.png"))]


def timeline(stops: list[tuple[float, float]], start_x: float) -> list[tuple[float, float]]:
    """[(t, x)] alternando llegada y salida de cada parada."""
    t, x = 0.0, start_x
    events = [(0.0, x)]
    for stop_x, wait in stops:
        t += abs(stop_x - x) / SPEED
        events.append((t, stop_x))
        t += wait
        events.append((t, stop_x))
        x = stop_x
    return events


def banner(t: dict, mobile: bool = False) -> str:
    """En móvil se recorta la parte derecha de la escena (Monserrate y el
    cohete), el nombre va en dos líneas y el recorrido es más corto."""
    bg_w, bg_h = 400, 169
    cx0 = 200 if mobile else 0  # columna nativa donde empieza el encuadre
    W, H = (bg_w - cx0) * S, bg_h * S
    m = 24 if mobile else 64
    d = ba.THEMES["dark"]

    walk, typing = frames("walk"), frames("type")
    stand = walk[0]
    bulb = px.from_png(PIX / "hero" / "bulb0.png")
    rocket = px.from_png(PIX / "rocket.png")
    rx, ry = (int(v) for v in (PIX / "rocket.txt").read_text().split())

    hero_w, hero_h = len(stand[0]) * S, len(stand) * S
    feet = GROUND * S
    rxs = (rx - cx0) * S  # x del cohete dentro del encuadre
    stops_x = [104, 196, 300, rxs - hero_w - 10] if mobile else [470, 640, 810, rxs - hero_w - 10]
    events = timeline(list(zip(stops_x, [2.4, 1.8, 3.2, 3.6])), m)
    period = round(events[-1][0] + 0.6, 2)
    arrive = [events[i][0] for i in range(1, len(events), 2)]
    leave = [events[i][0] for i in range(2, len(events), 2)]
    launch = arrive[3] + 0.7
    lift_end = launch + 2.4
    pct = lambda s: f"{100 * s / period:.3f}%"

    out = [f'<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath><g clip-path="url(#c)">',
           f'<image href="{px.png_data_uri(PIX / "bg-bogota.png")}" x="{-cx0 * S}" width="{bg_w * S}" height="{H}" '
           f'preserveAspectRatio="none" style="image-rendering:crisp-edges;image-rendering:pixelated"/>']
    for sx in stops_x:  # banderas de los 4 pasos
        out.append(f'<g shape-rendering="crispEdges">{px.sprite_svg(sp.FLAG, sp.FLAG_PAL, S, sx + hero_w / 2 - 3, feet - len(sp.FLAG) * S)}</g>')

    flame = "".join(f'<g class="fl{i}">{px.sprite_svg(f, {"y": "#F2C14E", "r": "#F28C4B"}, S, 0, len(rocket) * S)}</g>'
                    for i, f in enumerate(FLAME))
    out.append(f'<g shape-rendering="crispEdges" transform="translate({rxs} {ry * S})"><g class="rocket">'
               f'{px.to_paths(rocket, S)}<g class="flame">{flame}</g></g></g>')

    walk_svg = "".join(f'<g class="wk{i}">{px.to_paths(g, S)}</g>' for i, g in enumerate(walk))
    type_w = len(typing[0][0]) * S
    type_svg = "".join(f'<g class="ty{i}">{px.to_paths(g, S, -type_w * 0.3, hero_h - len(g) * S)}</g>'
                       for i, g in enumerate(typing))
    bulb_svg = px.to_paths(bulb, S, hero_w / 2 - len(bulb[0]) * S / 2 + 6, -len(bulb) * S - 4)
    blue_svg = px.sprite_svg(sp.BLUEPRINT, sp.BLUEPRINT_PAL, S, hero_w / 2 - 12, -len(sp.BLUEPRINT) * S - 8)
    shadow = f'<rect x="{S * 2}" y="{hero_h - 3}" width="{hero_w - S * 4}" height="6" rx="3" fill="#000" fill-opacity=".35"/>'
    out.append(f'<g shape-rendering="crispEdges" transform="translate({m} {feet - hero_h})"><g class="hero">'
               f'<g class="body">{shadow}<g class="hop"><g class="p-walk">{walk_svg}</g>'
               f'<g class="p-stand">{px.to_paths(stand, S)}</g></g></g>'
               f'<g class="p-type">{type_svg}</g><g class="p-bulb">{bulb_svg}</g><g class="p-blue">{blue_svg}</g></g></g>')
    out.append("</g>")

    out.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" stroke="{t["border"]}"/>')
    k, o = 14, 10
    out.append(f'<path d="M{o} {o + k}V{o}H{o + k}M{W - o - k} {o}H{W - o}V{o + k}M{W - o} {H - o - k}V{H - o}H{W - o - k}'
               f'M{o + k} {H - o}H{o}V{H - o - k}" stroke="#22C3D6" stroke-width="1.5" stroke-opacity=".7"/>')

    def shadowed(face, s, x, y, size, fill, **kw):
        """Texto con sombra en escalón, al estilo pixel."""
        return ba.text(face, s, x + 3, y + 3, size, "#06121B", **kw) + ba.text(face, s, x, y, size, fill, **kw)

    role = "Cofundador y COO de Magnor"
    if mobile:
        out.append(shadowed(ba.MONO[500], "BOGOTÁ, COLOMBIA", m, 58, 18, d["muted"], track=0.08))
        out.append(shadowed(ba.SANS[700], "Jesús Nicolás", m, 118, 54, d["text"], track=-0.01))
        out.append(shadowed(ba.SANS[700], "Pachón Suárez", m, 174, 54, d["text"], track=-0.01))
        rsize, ry0 = 25, 214
        out.append(shadowed(ba.MONO[500], role, m, ry0, rsize, d["accent_text"]))
        cx = m + ba.MONO[500].width(role, rsize) + 6
        out.append(f'<rect class="cur" x="{ba._num(cx)}" y="{ry0 - 20}" width="11" height="24" fill="#22C3D6"/>')
        out.append(ba.text(ba.SANS[600], "De la idea a producción.", m, feet + 52, 30, d["text"]))
    else:
        out.append(shadowed(ba.MONO[500], "BOGOTÁ, COLOMBIA  ·  SOFTWARE A MEDIDA Y PRODUCTOS PROPIOS", m, 76, 14, d["muted"], track=0.08))
        out.append(shadowed(ba.MONO[400], "4.711° N  74.072° W", W - m, 76, 14, d["muted"], anchor="end", track=0.08))
        out.append(shadowed(ba.SANS[700], "Jesús Nicolás Pachón Suárez", m, 150, 60, d["text"], track=-0.01))
        out.append(shadowed(ba.MONO[500], role, m, 196, 24, d["accent_text"]))
        cx = m + ba.MONO[500].width(role, 24) + 8
        out.append(f'<rect class="cur" x="{ba._num(cx)}" y="176" width="12" height="24" fill="#22C3D6"/>')
        out.append(ba.text(ba.SANS[600], "De la idea a producción.", m, feet + 50, 28, d["text"]))
        for sx, (num, name, _) in zip(stops_x, ba.STEPS):
            out.append(ba.label(f"{num} {name}", sx + hero_w / 2, feet + 30, d["muted"], 12, anchor="middle"))

    # --- animación
    css = [px.cycle_css("wk", len(walk), 0.6), px.cycle_css("ty", len(typing), 0.45), px.cycle_css("fl", 2, 0.16),
           ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"]
    move = "".join(f"{pct(tt)}{{transform:translateX({x - m:.1f}px)}}" for tt, x in events)
    css.append(f".hero{{animation:path {period}s linear infinite}}@keyframes path{{{move}100%{{transform:translateX({events[-1][1] - m:.1f}px)}}}}")
    css.append(f".hero{{opacity:1}}.body{{animation:fade {period}s steps(1) infinite}}"
               f"@keyframes fade{{0%{{opacity:1}}{pct(arrive[2])}{{opacity:0}}{pct(leave[2])}{{opacity:1}}{pct(events[-1][0])}{{opacity:0}}}}")

    def window(cls: str, spans: list[tuple[float, float]], base: int = 0) -> str:
        kf = "".join(f"{pct(a)}{{opacity:1}}{pct(b)}{{opacity:0}}" for a, b in spans)
        return f".{cls}{{opacity:{base};animation:v-{cls} {period}s steps(1) infinite}}@keyframes v-{cls}{{0%{{opacity:0}}{kf}}}"

    walking = [(leave[i - 1] if i else 0.0, arrive[i]) for i in range(4)]
    css.append(window("p-walk", walking))
    css.append(window("p-stand", [(arrive[0], leave[0]), (arrive[1], leave[1]), (arrive[3], events[-1][0])], base=1))
    css.append(window("p-type", [(arrive[2], leave[2])]))
    css.append(window("p-bulb", [(arrive[0] + 0.6, leave[0])]))
    css.append(window("p-blue", [(arrive[1] + 0.3, leave[1])]))
    hops = "".join(f"{pct(launch - 0.3 + j * 0.5)}{{transform:translateY(0)}}{pct(launch - 0.05 + j * 0.5)}{{transform:translateY(-15px)}}"
                   for j in range(5))
    css.append(f".hop{{animation:hop {period}s linear infinite}}@keyframes hop{{0%{{transform:translateY(0)}}{hops}"
               f"{pct(launch + 2.3)},100%{{transform:translateY(0)}}}}")
    up = ry * S + 140
    css.append(f".rocket{{animation:lift {period}s ease-in infinite}}@keyframes lift{{0%,{pct(launch)}{{transform:translateY(0);opacity:1}}"
               f"{pct(lift_end)}{{transform:translateY(-{up}px);opacity:1}}{pct(lift_end + 0.05)},{pct(period - 0.05)}{{transform:translateY(-{up}px);opacity:0}}"
               f"100%{{transform:translateY(0);opacity:1}}}}")
    css.append(f".flame{{opacity:0;animation:v-flame {period}s steps(1) infinite}}"
               f"@keyframes v-flame{{0%{{opacity:0}}{pct(launch - 0.3)}{{opacity:1}}{pct(lift_end)}{{opacity:0}}}}")

    title = "Jesús Nicolás Pachón Suárez · Cofundador y COO de Magnor · De la idea a producción"
    return ba.svg(W, H, title, "".join(out), "".join(css))
