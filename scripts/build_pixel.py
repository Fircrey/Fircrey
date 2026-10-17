"""Banner en pixel art: skyline de Bogotá con Monserrate, personaje que camina
por los 4 pasos y cohete que despega al llegar ("De la idea a producción").

Los sprites están en scripts/sprites.py; para cambiar de personaje solo hay que
sustituir ese archivo. Uso: lo invoca build_assets.py.
"""

from __future__ import annotations

import random

import build_assets as ba
import pixel as px
import sprites as sp

S = 4                   # píxeles de pantalla por celda
GW, GH = 300, 115       # cuadrícula: 1200 x 460
GROUND = 92             # fila donde pisa el personaje
PERIOD = 14.0           # segundos del ciclo completo


def sky(g: px.Grid) -> None:
    bands = [(0, "#08161F"), (12, "#0A1B27"), (24, "#0B1F2D"), (36, "#0D2536"),
             (47, "#102F41"), (57, "#143C4F"), (65, "#1A5063"), (72, "#1B5F72"), (78, "#1F8296")]
    for y in range(GH):
        color = [c for start, c in bands if y >= start][-1]
        px.rect(g, 0, y, GW, 1, color)


def stars(g: px.Grid, rng: random.Random) -> None:
    px.scatter(g, rng, 150, (0, 2, GW, 52), "#2B5B73", avoid=(10, 12, 295, 46))
    px.scatter(g, rng, 26, (0, 2, GW, 40), "#9FE7F0", avoid=(10, 12, 295, 46))


def monserrate(g: px.Grid) -> None:
    peak_x, peak_y = 246, 42
    for x in range(180, GW):
        slope = 0.62 if x < peak_x else 0.45
        top = int(peak_y + abs(x - peak_x) * slope)
        px.rect(g, x, top, 1, GROUND - top, "#14405A")
        g[top][x] = "#2A7C96"  # filo de la cresta
        if top + 1 < GROUND:
            g[top + 1][x] = "#1D5C75"
    # ermita en la cumbre
    px.stamp(g, sp.CHURCH, sp.CHURCH_PAL, peak_x - 3, peak_y - 6)


def skyline(g: px.Grid, rng: random.Random) -> None:
    x = 0
    while x < GW:  # fondo
        w, h = rng.randint(9, 16), rng.randint(22, 40) if x > 120 else rng.randint(14, 24)
        px.rect(g, x, GROUND - h, w, h, "#0E2B3B")
        x += w
    x = rng.randint(0, 4)
    while x < GW:  # frente, con ventanas
        w, h = rng.randint(8, 14), rng.randint(10, 22) if x > 120 else rng.randint(6, 14)
        top = GROUND - h
        px.rect(g, x, top, w, h, "#071520")
        for wy in range(top + 2, GROUND - 2, 3):
            for wx in range(x + 1, x + w - 1, 2):
                r = rng.random()
                if r < 0.22:
                    g[wy][wx] = "#22C3D6"
                elif r < 0.30:
                    g[wy][wx] = "#F2C14E"
        x += w + rng.randint(0, 2)


def ground(g: px.Grid) -> None:
    px.rect(g, 0, GROUND, GW, GH - GROUND, "#0B1E2B")
    px.rect(g, 0, GROUND, GW, 2, "#13738A")
    px.rect(g, 0, GROUND + 2, GW, 1, "#0F4A5C")
    for x in range(0, GW, 10):
        px.rect(g, x + 2, GROUND + 6, 5, 1, "#12384B")


def checkpoints(g: px.Grid, cols: list[int]) -> None:
    for c in cols:
        px.stamp(g, sp.FLAG, sp.FLAG_PAL, c, GROUND - len(sp.FLAG))


def banner(t: dict) -> str:
    rng = random.Random(97)
    W, H = GW * S, GH * S
    g = px.new_grid(GW, GH)
    sky(g)
    stars(g, rng)
    monserrate(g)
    skyline(g, rng)
    ground(g)

    # texto (siempre sobre cielo oscuro, con los colores del tema oscuro)
    d = ba.THEMES["dark"]
    m = 64
    tag = "De la idea a producción."
    tag_end = m + ba.SANS[600].width(tag, 34)
    x0, x1 = tag_end + 90, 960
    cols = [int((x0 + (x1 - x0) * i / 3) / S) for i in range(4)]
    checkpoints(g, cols)

    out = [f'<clipPath id="c"><rect width="{W}" height="{H}" rx="18"/></clipPath>',
           f'<g clip-path="url(#c)" shape-rendering="crispEdges">{px.to_paths(g, S)}</g>']

    # rocket (despega al final del ciclo)
    rx = 280 * S
    rocket = px.sprite_svg(sp.ROCKET, sp.ROCKET_PAL, S)
    flame = px.sprite_svg(sp.FLAME, sp.FLAME_PAL, S)
    ry = (GROUND - len(sp.ROCKET)) * S
    fl_y = len(sp.ROCKET) * S
    out.append(f'<g shape-rendering="crispEdges" transform="translate({rx} {ry})"><g class="rocket">{rocket}'
               f'<g class="flame" transform="translate(0 {fl_y})">{flame}</g></g></g>')

    # personaje: 4 fotogramas de caminata
    cy = (GROUND - len(sp.WALK[0])) * S
    start = m
    frames = "".join(
        f'<g class="w w{i}">{px.sprite_svg(sp.WALK[order], sp.HERO_PAL, S)}</g>'
        for i, order in enumerate((0, 1, 2, 1)))
    shadow = f'<rect x="{3 * S}" y="{len(sp.WALK[0]) * S - 2}" width="{(len(sp.WALK[0][0]) - 6) * S}" height="4" fill="#000" fill-opacity=".35"/>'
    out.append(f'<g shape-rendering="crispEdges" transform="translate({start} {cy})"><g class="walker">{shadow}{frames}</g></g>')

    # marco del tema (borde y marcas de esquina)
    out.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="17.5" stroke="{t["border"]}"/>')
    k, o = 14, 10
    out.append(f'<path d="M{o} {o + k}V{o}H{o + k}M{W - o - k} {o}H{W - o}V{o + k}M{W - o} {H - o - k}V{H - o}H{W - o - k}M{o + k} {H - o}H{o}V{H - o - k}" '
               f'stroke="#22C3D6" stroke-width="1.5" stroke-opacity=".7"/>')

    out.append(ba.label("Bogotá, Colombia  ·  Software a medida y productos propios", m, 82, d["muted"], 14))
    out.append(ba.label("4.711° N  74.072° W", W - m, 82, d["muted"], 14, anchor="end", w=400))
    out.append(ba.text(ba.SANS[700], "Jesús Nicolás Pachón Suárez", m, 160, 62, d["text"], track=-0.01))
    role = "Cofundador y COO de Magnor"
    out.append(ba.text(ba.MONO[500], role, m, 210, 24, d["accent_text"]))
    cx = m + ba.MONO[500].width(role, 24) + 8
    out.append(f'<rect class="cur" x="{ba._num(cx)}" y="190" width="12" height="24" fill="#22C3D6"/>')
    out.append(ba.text(ba.SANS[600], tag, m, 438, 34, d["text"]))
    for c, (num, name, _) in zip(cols, ba.STEPS):
        out.append(ba.label(f"{num} {name}", c * S + 4, 412, d["muted"], 12, anchor="middle"))

    travel = (278 * S) - start - len(sp.WALK[0][0]) * S
    css = (
        ".w{opacity:0}.w0{opacity:1}"
        ".w{animation:step .8s steps(1) infinite}"
        ".w0{animation-name:s0}.w1{animation-name:s1}.w2{animation-name:s2}.w3{animation-name:s3}"
        "@keyframes s0{0%{opacity:1}25%,100%{opacity:0}}"
        "@keyframes s1{0%,24.9%{opacity:0}25%{opacity:1}50%,100%{opacity:0}}"
        "@keyframes s2{0%,49.9%{opacity:0}50%{opacity:1}75%,100%{opacity:0}}"
        "@keyframes s3{0%,74.9%{opacity:0}75%{opacity:1}100%{opacity:0}}"
        f".walker{{animation:walk {PERIOD}s linear infinite}}"
        f"@keyframes walk{{0%{{transform:translateX(0);opacity:1}}72%{{transform:translateX({travel}px);opacity:1}}"
        f"73%,100%{{transform:translateX({travel}px);opacity:0}}}}"
        f".rocket{{animation:lift {PERIOD}s ease-in infinite}}"
        f"@keyframes lift{{0%,74%{{transform:translateY(0);opacity:1}}95%{{transform:translateY(-440px);opacity:1}}96%,100%{{transform:translateY(-440px);opacity:0}}}}"
        f".flame{{opacity:0;animation:fire {PERIOD}s steps(1) infinite}}"
        "@keyframes fire{0%,74%{opacity:0}75%,95%{opacity:1}96%,100%{opacity:0}}"
        ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    )
    title = "Jesús Nicolás Pachón Suárez · Cofundador y COO de Magnor · De la idea a producción"
    return ba.svg(W, H, title, "".join(out), css)
