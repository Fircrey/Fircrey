"""Versiones móviles de las piezas del perfil (sufijo -m).

En un teléfono el README mide unos 308 px de ancho: una pieza de 1200 px se
ve al 26 % y su texto queda ilegible. Estas versiones se diseñan a 600 px
(o más grandes aún, las tarjetas que van a media anchura) y en vertical.
El README las sirve con <source media="(max-width: 600px)">.
"""

from __future__ import annotations

import build_assets as ba
from build_assets import MONO, SANS, _num, label, text

MW = 600
DARK = ba.THEMES["dark"]
SPEED = 650.0


def _frame(t: dict, w: float, h: float, inner: str, grid: bool = False) -> str:
    return (f'<clipPath id="c"><rect width="{w}" height="{h}" rx="18"/></clipPath>'
            f'<g clip-path="url(#c)"><rect width="{w}" height="{h}" fill="{t["bg"]}"/>{inner}</g>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="17.5" stroke="{t["border"]}"/>' + ba.corners(w, h))


def _wrap_draw(face, s: str, x: float, y: float, size: float, max_w: float, lh: float, fill: str) -> tuple[str, float]:
    lines = face.wrap(s, size, max_w)
    return "".join(text(face, ln, x, y + i * lh, size, fill) for i, ln in enumerate(lines)), y + (len(lines) - 1) * lh


# ---------------------------------------------------------------- intro

def intro(t: dict) -> str:
    import pixel

    S, size, lh = 4, 25, 36
    px0, py0 = 14, 46
    box_w = MW - 2 * px0
    fx, fy, fw, fh = px0 + 30, py0 + 32, 150, 176
    lines = SANS[400].wrap(ba.INTRO, size, box_w - 2 * 46)
    y0 = fy + fh + 54
    bh = (y0 - py0) + (len(lines) - 1) * lh + 58
    h = py0 + bh + 18
    bg = "#0B1E2B"
    b = [f'<rect x="{px0}" y="{py0}" width="{box_w}" height="{bh}" fill="{bg}"/>',
         f'<rect x="{px0 + 3}" y="{py0 + 3}" width="{box_w - 6}" height="{bh - 6}" stroke="#E6F3F6" stroke-width="6" shape-rendering="crispEdges"/>',
         f'<rect x="{px0 + 12}" y="{py0 + 12}" width="{box_w - 24}" height="{bh - 24}" stroke="#22C3D6" stroke-width="3" shape-rendering="crispEdges"/>',
         f'<rect x="{px0 + 6}" y="{py0 + bh}" width="{box_w}" height="6" fill="#06121B"/>',
         f'<rect x="{px0 + box_w}" y="{py0 + 6}" width="6" height="{bh}" fill="#06121B"/>',
         f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#10293A" stroke="#22C3D6" stroke-width="3" shape-rendering="crispEdges"/>']
    busts = [pixel.from_png(ba.PIXEL / "portrait" / f"idle{i}.png") for i in range(2)]
    bw, bht = len(busts[0][0]) * S, len(busts[0]) * S
    ox, oy = fx + (fw - bw) / 2, fy + fh - bht
    b.append(f'<g shape-rendering="crispEdges"><g class="pb0">{pixel.to_paths(busts[0], S, ox, oy)}</g>'
             f'<g class="pb1">{pixel.to_paths(busts[1], S, ox, oy)}</g></g>')
    rx = fx + fw + 26
    b.append(text(SANS[600], "Cofundador y COO", rx, fy + 58, 30, "#E6F3F6"))
    b.append(text(SANS[600], "de ", rx, fy + 98, 30, "#E6F3F6"))
    b.append(text(SANS[600], "Magnor", rx + SANS[600].width("de ", 30), fy + 98, 30, "#22C3D6"))
    b.append(label("Bogotá, Colombia", rx, fy + 146, "#8EA8B5", 17))
    name = "JESÚS PACHÓN"
    nw = MONO[500].width(name, 18, 0.1) + 40
    b.append(f'<rect x="{px0 + 34}" y="{py0 - 18}" width="{_num(nw)}" height="44" fill="#06121B"/>'
             f'<rect x="{px0 + 30}" y="{py0 - 22}" width="{_num(nw)}" height="44" fill="#22C3D6"/>')
    b.append(text(MONO[500], name, px0 + 50, py0 + 7, 18, "#0B1E2B", track=0.1))
    t0 = 0.6
    tx = px0 + 46
    for i, line in enumerate(lines):
        y = y0 + i * lh
        k = line.find("Magnor")
        if k < 0:
            b.append(text(SANS[400], line, tx, y, size, "#E6F3F6"))
        else:
            pre, post = line[:k], line[k + 6:]
            b.append(text(SANS[400], pre, tx, y, size, "#E6F3F6"))
            b.append(text(SANS[400], "Magnor", tx + SANS[400].width(pre, size), y, size, "#22C3D6"))
            b.append(text(SANS[400], post, tx + SANS[400].width(pre + "Magnor", size), y, size, "#E6F3F6"))
        lw = SANS[400].width(line, size) + 12
        dur = len(line) / ba.TYPE_CPS
        b.append(f'<rect class="tp" style="animation-duration:{dur:.2f}s;animation-delay:{t0:.2f}s;'
                 f'animation-timing-function:steps({len(line)})" x="{tx - 2}" y="{y - size - 5}" width="{_num(lw + 4)}" height="{lh}" fill="{bg}"/>')
        t0 += dur + 0.12
    b.append(f'<path class="nx" style="animation-delay:{t0:.2f}s" d="M{px0 + box_w - 58} {py0 + bh - 44}h20l-10 11z" fill="#22C3D6"/>')
    css = (".tp{transform-box:fill-box;transform-origin:100% 50%;transform:scaleX(0);animation-name:tp;animation-fill-mode:both}"
           "@keyframes tp{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
           ".nx{animation:nx 1s steps(1) infinite both}@keyframes nx{0%{opacity:1}50%{opacity:0}}"
           + pixel.vis_css("pb1", [(3.2, 3.5)], 3.5) + ".pb0{opacity:1}")
    return ba.svg(MW, h, "Jesús Pachón: " + ba.INTRO, "".join(b), css)


# ---------------------------------------------------------------- cifras y secciones

def impact(t: dict) -> str:
    m, cw, rh, top = 28, (MW - 56) / 2, 196, 26
    h = top + rh * 2 + 10
    b = []
    for i, (value, desc) in enumerate(ba.IMPACT):
        col, row = i % 2, i // 2
        x, y = m + col * cw + 18, top + row * rh
        b.append(f'<rect x="{_num(x)}" y="{y + 18}" width="34" height="4" fill="{t["accent"]}"/>')
        vsize = 50 if SANS[700].width(value, 50) < cw - 36 else 38
        b.append(text(SANS[700], value, x, y + 80, vsize, t["text"], track=-0.02))
        body, _ = _wrap_draw(SANS[400], desc, x, y + 118, 22, cw - 40, 29, t["muted"])
        b.append(body)
    b.append(f'<path d="M{MW / 2} {top + 14}V{top + rh * 2 - 14}M{m + 10} {top + rh}H{MW - m - 10}" stroke="{t["border"]}"/>')
    title = "Impacto: " + " · ".join(f"{v} {d}" for v, d in ba.IMPACT)
    return ba.svg(MW, h, title, _frame(t, MW, h, "".join(b)))


def section(t: dict, num: str, name: str) -> str:
    h = 74
    b = [label(num, 2, 48, t["accent_text"], 22), label(name, 50, 48, t["text"], 22)]
    nx = 50 + MONO[500].width(name.upper(), 22, 0.08) + 20
    b.append(f'<path d="M{_num(nx)} 40H{MW - 2}" stroke="{t["border"]}" stroke-width="1.5"/>')
    return ba.svg(MW, h, f"{num} {name}", "".join(b))


# ---------------------------------------------------------------- tarjetas

def _split_title(p: dict) -> tuple[str, str]:
    name, _, sub = p["title"].replace(" ", " ").partition(" · ")
    return name, sub


def tile_height(p: dict) -> float:
    _, sub = _split_title(p)
    return 8 + 330 + 70 + 90 + 50 * len(SANS[500].wrap(sub, 40, 530)) + 150


def tile(t: dict, p: dict, h: float) -> str:
    """Tarjeta de media anchura en móvil: se ve a unos 150 px, así que el texto
    es enorme y solo dice lo esencial. El detalle está en el caso de estudio."""
    w, o = 600, 8
    name, sub = _split_title(p)
    b = [ba.frame(t, o, o, w - 2 * o, h - 2 * o, r=22, grid=False),
         f'<clipPath id="ca"><rect x="{o}" y="{o}" width="{w - 2 * o}" height="{h - 2 * o}" rx="22"/></clipPath>',
         f'<g clip-path="url(#ca)">{ba.scene(p["art"], o, o, w - 2 * o, 330)}</g>',
         f'<path d="M{o} {o + 330}H{w - o}" stroke="{t["border"]}" stroke-width="2"/>']
    y = o + 330 + 70
    if p["status"]:
        b.append(f'<circle cx="52" cy="{y - 12}" r="11" fill="{t["accent"]}"/>')
        b.append(label(p["status"], 76, y, t["accent_text"], 30))
    y += 90
    b.append(text(SANS[700], name, 40, y, 66, t["text"], track=-0.02))
    body, y = _wrap_draw(SANS[500], sub, 40, y + 58, 40, 530, 50, t["muted"])
    b.append(body)
    btn, _ = ba.rpg_button(t, "VER CASO", 40, h - o - 112, 32, 84)
    b.append(btn)
    return ba.svg(w, h, f'{p["title"]}. {p["what"]} {p["result"]}', "".join(b))


def wide_card(t: dict, p: dict) -> str:
    """La tarjeta ancha (magnor.tech) en móvil: arte arriba y texto debajo."""
    w, o, pad = MW, 8, 34
    tw = w - 2 * o - 2 * pad
    title = SANS[700].wrap(p["title"].replace(" ", " "), 36, tw)
    what = SANS[400].wrap(p["what"], 24, tw)
    result = SANS[500].wrap(p["result"], 25, tw - 34)
    art_h = 300
    h = o + art_h + 64 + 46 * len(title) + 14 + 33 * len(what) + 14 + 34 * len(result) + 40 + 60 + 50 + 80 + o
    b = [ba.frame(t, o, o, w - 2 * o, h - 2 * o, r=18, grid=False),
         f'<clipPath id="ca"><rect x="{o}" y="{o}" width="{w - 2 * o}" height="{h - 2 * o}" rx="18"/></clipPath>',
         f'<g clip-path="url(#ca)">{ba.scene(p["art"], o, o, w - 2 * o, art_h)}</g>',
         f'<path d="M{o} {o + art_h}H{w - o}" stroke="{t["border"]}" stroke-width="2"/>']
    x0 = o + pad
    y = o + art_h + 54
    if p["status"]:
        b.append(f'<circle cx="{x0 + 8}" cy="{y - 7}" r="7" fill="{t["accent"]}"/>')
        b.append(label(p["status"], x0 + 26, y, t["accent_text"], 19))
    b.append(label(p["kind"], w - o - pad, y, t["muted"], 17, anchor="end"))
    y += 58
    for ln in title:
        b.append(text(SANS[700], ln, x0, y, 36, t["text"], track=-0.01))
        y += 46
    y += 6
    for ln in what:
        b.append(text(SANS[400], ln, x0, y, 24, t["muted"]))
        y += 33
    y += 10
    b.append(text(SANS[500], "→", x0, y, 25, t["accent_text"]))
    for ln in result:
        b.append(text(SANS[500], ln, x0 + 34, y, 25, t["text"]))
        y += 34
    y += 16
    cx = x0
    for c in p["chips"]:
        body, cw = ba.chip(t, c, 0, 0, 13)
        k = 1.45
        if cx + cw * k > w - o - pad:
            break
        b.append(f'<g transform="translate({_num(cx)} {_num(y)}) scale({k})">{body}</g>')
        cx += cw * k + 10
    y += 60
    b.append(text(MONO[400], p["stack"], x0, y + 10, 19, t["muted"]))
    btn, _ = ba.rpg_button(t, "VER CASO", x0, h - o - 96, 22, 64)
    b.append(btn)
    return ba.svg(w, h, f'{p["title"]}. {p["what"]} {p["result"]} Stack: {p["stack"]}.', "".join(b), ba.PULSE_CSS)


# ---------------------------------------------------------------- stack

def stack(t: dict) -> str:
    """Las capas apiladas en vertical; el árbol, abajo, lanza la onda hacia
    arriba y cada insignia tiembla al pasarle, sin caerse."""
    import pixel

    k, m = 1.45, 30
    S = 3
    groups = [("Lenguajes", ba.LANGUAGES)] + list(ba.STACK)
    placed, y = [], 40
    for layer, items in groups:
        placed.append(("label", layer, m, y + 22))
        y += 44
        x = m
        for item in items:
            body, bw = ba.badge(t, item, 0, 0)
            bw *= k
            if x + bw > MW - m:
                x, y = m, y + 54
            placed.append(("badge", body, x, y, bw))
            x += bw + 10
        y += 54 + 26
        placed.append(("rule", None, m, y - 14))
    tree = {n: pixel.from_png(ba.PIXEL / "tree" / f"{n}.png") for n in ("idle0", "idle1", "prep0", "blast0")}
    tw = max(len(g[0]) for g in tree.values()) * S
    th = max(len(g) for g in tree.values()) * S
    tx, ty = MW - m - tw, y
    h = ty + th + 30
    mouth_x, mouth_y = tx + 10, ty + th * 0.45

    def hit(cy: float) -> str:
        return f"{ba.TREE_EMIT + max(mouth_y - cy, 0) / SPEED:.2f}s"

    b = []
    for item in placed:
        if item[0] == "label":
            b.append(label(item[1], item[2], item[3], t["accent_text"], 20))
        elif item[0] == "rule":
            b.append(f'<path d="M{m} {item[3]}H{MW - m}" stroke="{t["border"]}"/>')
        else:
            _, body, x, yy, bw = item
            b.append(f'<g class="q" style="animation-delay:{hit(yy + 22)}"><g transform="translate({_num(x)} {_num(yy)}) scale({k})">{body}</g></g>')
    blocks = []
    for kk, color in enumerate(("#E6F3F6", "#22C3D6", "#22C3D6")):
        R, span = 420 + kk * 30, 270
        edge = (R * R - span * span) ** 0.5
        for xx in range(-span, span + 1, 6):
            yy = -((R * R - xx * xx) ** 0.5 - edge) - kk * 24
            blocks.append(f'<rect x="{xx}" y="{round(yy / 6) * 6}" width="6" height="6" fill="{color}"/>')
    travel = mouth_y - 20
    b.append(f'<clipPath id="cw"><rect width="{MW}" height="{h}" rx="18"/></clipPath>'
             f'<g clip-path="url(#cw)"><g transform="translate({MW / 2} {_num(mouth_y)})">'
             f'<g class="wave" shape-rendering="crispEdges">{"".join(blocks)}</g></g></g>')

    def sprite(n: str, cls: str) -> str:
        g = tree[n]
        gw, gh = len(g[0]) * S, len(g) * S
        ox, oy = tx + (tw - gw) / 2, ty + th - gh
        return f'<g class="{cls}" transform="translate({_num(ox + gw)} {_num(oy)}) scale(-1 1)">{pixel.to_paths(g, S)}</g>'

    b.append(f'<rect x="{tx + 14}" y="{ty + th - 4}" width="{tw - 28}" height="8" rx="4" fill="#000" fill-opacity=".35"/>')
    b.append(f'<g shape-rendering="crispEdges"><g class="t-idle">{sprite("idle0", "ti0")}{sprite("idle1", "ti1")}</g>'
             f'{sprite("prep0", "t-prep")}{sprite("blast0", "t-blast")}</g>')
    P, e = ba.TREE_PERIOD, ba.TREE_EMIT
    end = e + travel / SPEED
    css = [pixel.cycle_css("ti", 2, 0.5),
           pixel.vis_css("t-idle", [(0, e - 0.6), (e + 1.3, P)], P, base=1),
           pixel.vis_css("t-prep", [(e - 0.6, e)], P),
           pixel.vis_css("t-blast", [(e, e + 1.3)], P),
           f".wave{{opacity:0;animation:wave {P}s linear infinite}}"
           f"@keyframes wave{{0%,{100 * e / P:.2f}%{{transform:translateY(0);opacity:0}}"
           f"{100 * (e + 0.1) / P:.2f}%{{opacity:.95}}{100 * (end - 0.15) / P:.2f}%{{opacity:.85}}"
           f"{100 * end / P:.2f}%{{transform:translateY(-{_num(travel)}px);opacity:0}}100%{{opacity:0}}}}",
           ".q{transform-box:fill-box;transform-origin:50% 100%;animation:quake " + f"{P}s linear infinite" + "}"
           "@keyframes quake{0%{transform:none}1.2%{transform:translate(-3px,0) rotate(-2deg)}"
           "2.4%{transform:translate(3px,-1px) rotate(1.6deg)}3.6%{transform:translate(-2px,0) rotate(-1deg)}"
           "4.8%{transform:translate(1px,0) rotate(.5deg)}6%,100%{transform:none}}"]
    title = "Stack por capas. Lenguajes: " + ", ".join(ba.LANGUAGES) + ". " + ". ".join(
        f"{layer}: {', '.join(items)}" for layer, items in ba.STACK) + "."
    return ba.svg(MW, h, title, _frame(t, MW, h, "".join(b)), "".join(css))


# ---------------------------------------------------------------- cómo trabajo

def process(t: dict) -> str:
    art_h = 231
    spine = 44
    period = 8.0
    y = art_h + 66
    rows = []
    for num, name, desc in ba.STEPS:
        lines = SANS[400].wrap(desc, 23, MW - 120)
        rows.append((y, num, name, lines))
        y += 46 + len(lines) * 31 + 34
    h = y + 4
    y_first, y_last = rows[0][0] - 9, rows[-1][0] - 9
    b = [ba.scene("process", 0, 0, MW, art_h), f'<path d="M0 {art_h}H{MW}" stroke="#22C3D6" stroke-opacity=".5"/>',
         f'<path class="flow" d="M{spine} {y_first}V{y_last}" stroke="#22C3D6" stroke-width="3" stroke-linecap="square"/>']
    for yy, num, name, lines in rows:
        at = period * (yy - y_first) / max(y_last - y_first, 1)
        b.append(f'<rect x="{spine - 8}" y="{yy - 17}" width="16" height="16" fill="#0B1E2B" stroke="#22C3D6" stroke-width="3"/>')
        b.append(f'<rect class="lit" style="--p:{period}s;animation-delay:{ba.lit_delay(at, period)}" '
                 f'x="{spine - 4}" y="{yy - 13}" width="8" height="8" fill="#22C3D6"/>')
        b.append(label(num, 78, yy, "#22C3D6", 19))
        b.append(text(SANS[600], name, 120, yy + 1, 30, "#E6F3F6"))
        for j, ln in enumerate(lines):
            b.append(text(SANS[400], ln, 78, yy + 42 + j * 31, 23, "#8EA8B5"))
    dark = dict(t, bg="#0B1E2B")
    title = "Cómo trabajo: " + " → ".join(f"{n}: {d}" for _, n, d in ba.STEPS)
    return ba.svg(MW, h, title, _frame(dark, MW, h, "".join(b)), ba.flow_css(y_last - y_first, period))


# ---------------------------------------------------------------- cierre

def cta(t: dict) -> str:
    art_h, m = 330, 34
    y = art_h + 66
    b = [ba.scene("cta", 0, 0, MW, art_h).replace("xMidYMid slice", "xMaxYMid slice"),
         f'<path d="M0 {art_h}H{MW}" stroke="#22C3D6" stroke-opacity=".5"/>',
         label("¿Tienes un proyecto?", m, y, "#22C3D6", 19)]
    y += 62
    for ln in ("Lo llevamos de la idea", "a producción."):
        b.append(text(SANS[700], ln, m, y, 42, "#E6F3F6", track=-0.01))
        y += 52
    body, y = _wrap_draw(SANS[400], "Requerimientos, arquitectura, desarrollo web y móvil, integraciones y despliegue.",
                         m, y + 6, 24, MW - 2 * m, 33, "#B9CFD8")
    b.append(body)
    dark = dict(t, bg="#0B1E2B", text="#E6F3F6")
    btn, _ = ba.rpg_button(dark, "ESCRÍBEME", m, y + 34, 22, 66)
    b.append(btn)
    y += 34 + 66 + 52
    b.append(label("Bogotá, Colombia", m, y, "#8EA8B5", 16, w=400))
    b.append(label("Trabajo en remoto con clientes de cualquier país", m, y + 28, "#8EA8B5", 16, w=400))
    h = y + 56
    return ba.svg(MW, h, "¿Tienes un proyecto? Lo llevamos de la idea a producción. Escríbeme.",
                  _frame(dark, MW, h, "".join(b)))


# ---------------------------------------------------------------- estadísticas (plantilla)

def stats_template(t: dict) -> tuple[str, list[dict], dict]:
    top = 200
    rh, cw, m = 150, (MW - 60) / 2, 30
    h = top + rh * 2 + 64
    seal_svg, seal_css = ba.seal(ba.STATS_ART)
    b = [f'<g transform="scale(.5)">{ba.scene("office", 0, 0, 1200, ba.STATS_ART)}{seal_svg}</g>',
         f'<path d="M0 {top}H{MW}" stroke="#22C3D6" stroke-opacity=".5"/>']
    slots = []
    for i, (key, desc) in enumerate(ba.STATS):
        col, row = i % 2, i // 2
        x, y = m + col * cw + 14, top + row * rh
        b.append(f'<rect x="{_num(x)}" y="{y + 28}" width="30" height="4" fill="{t["accent"]}"/>')
        b.append(f"<!--{key}-->")
        slots.append(dict(key=key, x=round(x, 1), y=y + 86))
        body, _ = _wrap_draw(SANS[400], desc, x, y + 118, 21, cw - 30, 27, t["muted"])
        b.append(body)
    b.append(f'<path d="M{MW / 2} {top + 20}V{top + rh * 2 - 6}M{m + 6} {top + rh}H{MW - m - 6}" stroke="{t["border"]}"/>')
    b.append("<!--updated-->")
    updated = dict(x=MW - m, y=h - 26, size=18)
    return ba.svg(MW, h, "__TITLE__", _frame(t, MW, h, "".join(b)), seal_css + "/*MOOD*/"), slots, updated


def build_all(write) -> dict:
    """Escribe todas las piezas -m y devuelve la meta de la plantilla de cifras."""
    import build_pixel

    tiles = [p for p in ba.PROJECTS if p.get("art")]
    th = max(tile_height(p) for p in tiles)
    meta = {}
    for name, t in ba.THEMES.items():
        write("banner-m", name, build_pixel.banner(t, mobile=True))
        write("intro-m", name, intro(t))
        write("impact-m", name, impact(t))
        for p in tiles:
            write(f"card-{p['slug']}-m", name, tile(t, p, th))
        write("card-magnor-m", name, wide_card(t, ba.MAGNOR))
        write("stack-m", name, stack(t))
        write("process-m", name, process(t))
        write("cta-m", name, cta(t))
        for key, (num, title, _) in ba.SECTIONS.items():
            write(f"section-{key}-m", name, section(t, num, title))
        tpl, slots, updated = stats_template(t)
        (ba.TEMPLATES / f"stats-m-{name}.svg").write_text(tpl, encoding="utf-8")
        meta = dict(slots=slots, updated=updated)
    return meta
