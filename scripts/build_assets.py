"""Genera los SVG estáticos del perfil en assets/ y las plantillas de estadísticas.

Todo el texto se convierte a trazos para que el diseño sea idéntico en cualquier
sistema (un SVG cargado con <img> no puede usar fuentes externas).

Uso:   python scripts/build_assets.py
Deps:  pip install fonttools uharfbuzz
Las fuentes (licencia OFL) se descargan en scripts/.fonts/ la primera vez.
"""

from __future__ import annotations

import json
import urllib.request
from html import escape
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
TEMPLATES = ROOT / "scripts" / "templates"
FONT_DIR = ROOT / "scripts" / ".fonts"
FONT_URLS = {
    "SpaceGrotesk.ttf": "https://github.com/google/fonts/raw/main/ofl/spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    "JetBrainsMono.ttf": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}

W = 1200  # ancho de referencia de todas las piezas anchas

THEMES = {
    "dark": dict(
        bg="#0B1E2B", panel="#0E2535", grid="#22C3D6", grid_op=0.10, border="#1D3B4E",
        text="#E6F3F6", muted="#8EA8B5", accent="#22C3D6", accent_text="#22C3D6",
        chip="#10293A", on_accent="#0B1E2B",
    ),
    "light": dict(
        bg="#F5F9FA", panel="#FFFFFF", grid="#0B1E2B", grid_op=0.07, border="#D2E0E6",
        text="#0B1E2B", muted="#4F6672", accent="#22C3D6", accent_text="#08707E",
        chip="#EAF4F6", on_accent="#0B1E2B",
    ),
}

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}.lit{opacity:1!important}}"


# ---------------------------------------------------------------- tipografía

def _font_path(name: str) -> Path:
    path = FONT_DIR / name
    if not path.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONT_URLS[name], path)
    return path


def _num(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Face:
    """Una fuente variable fijada a un peso: mide y convierte texto a trazos."""

    def __init__(self, file: str, wght: int):
        path = _font_path(file)
        self._hb = hb.Font(hb.Face(path.read_bytes()))
        self._hb.set_variations({"wght": wght})
        tt = instancer.instantiateVariableFont(TTFont(path), {"wght": wght})
        self._glyphs = tt.getGlyphSet()
        self._order = tt.getGlyphOrder()
        self.upem = tt["head"].unitsPerEm

    def _shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self._hb, buf, {"kern": True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text: str, size: float, track: float = 0) -> float:
        _, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem + track * size * max(len(pos) - 1, 0)

    def path(self, text: str, x: float, y: float, size: float, track: float = 0) -> str:
        infos, pos = self._shape(text)
        s = size / self.upem
        pen = SVGPathPen(self._glyphs, ntos=_num)
        cx = 0.0
        for info, p in zip(infos, pos):
            name = self._order[info.codepoint]
            ox = x + cx + p.x_offset * s
            self._glyphs[name].draw(TransformPen(pen, (s, 0, 0, -s, ox, y - p.y_offset * s)))
            cx += p.x_advance * s + track * size
        return pen.getCommands()

    def wrap(self, text: str, size: float, max_w: float, track: float = 0) -> list[str]:
        lines, cur = [], ""
        for word in text.split(" "):  # split() también cortaría en espacios duros
            trial = f"{cur} {word}".strip()
            if cur and self.width(trial, size, track) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines


SANS = {w: Face("SpaceGrotesk.ttf", w) for w in (400, 500, 600, 700)}
MONO = {w: Face("JetBrainsMono.ttf", w) for w in (400, 500)}


def text(face: Face, s: str, x: float, y: float, size: float, fill: str,
         anchor: str = "start", track: float = 0, cls: str = "") -> str:
    w = face.width(s, size, track)
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w / 2
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} fill="{fill}" d="{face.path(s, x, y, size, track)}"/>'


def label(s: str, x: float, y: float, fill: str, size: float = 13, anchor: str = "start", w: int = 500) -> str:
    """Etiqueta técnica: monoespaciada, mayúsculas y con tracking."""
    return text(MONO[w], s.upper(), x, y, size, fill, anchor, track=0.08)


# ---------------------------------------------------------------- piezas comunes

def svg(w: float, h: float, title: str, body: str, css: str = "") -> str:
    style = f"<style>{css}{REDUCED_MOTION}</style>" if css else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(w)}" height="{_num(h)}" '
        f'viewBox="0 0 {_num(w)} {_num(h)}" role="img" aria-labelledby="t" fill="none">'
        f'<title id="t">{escape(title)}</title>{style}{body}</svg>'
    )


def frame(t: dict, x: float, y: float, w: float, h: float, r: float = 18, grid: bool = True) -> str:
    """Panel de plano: fondo, retícula de puntos, borde y marcas de esquina."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{t["bg"]}"/>']
    if grid:
        out.append(
            f'<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse" x="{x + 12}" y="{y + 12}">'
            f'<circle cx="1" cy="1" r="1" fill="{t["grid"]}" fill-opacity="{t["grid_op"]}"/></pattern>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="url(#dots)"/>'
        )
    out.append(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r - .5}" stroke="{t["border"]}"/>')
    k, o = 14, 10  # longitud y separación de las marcas de esquina
    x0, y0, x1, y1 = x + o, y + o, x + w - o, y + h - o
    d = (f"M{x0} {y0 + k}V{y0}H{x0 + k}M{x1 - k} {y0}H{x1}V{y0 + k}"
         f"M{x1} {y1 - k}V{y1}H{x1 - k}M{x0 + k} {y1}H{x0}V{y1 - k}")
    out.append(f'<path d="{d}" stroke="{t["accent"]}" stroke-width="1.5" stroke-opacity=".7"/>')
    return "".join(out)


def chip(t: dict, s: str, x: float, y: float, size: float = 14) -> tuple[str, float]:
    """Etiqueta con borde; devuelve (svg, ancho)."""
    f = MONO[500]
    tw = f.width(s, size)
    w, h = tw + 24, size + 16
    body = (f'<rect x="{x}" y="{y}" width="{_num(w)}" height="{h}" rx="{h / 2}" fill="{t["chip"]}" stroke="{t["border"]}"/>'
            + text(f, s, x + 12, y + h / 2 + size * 0.36, size, t["text"]))
    return body, w


def status(t: dict, s: str, x: float, y: float, live: bool = True) -> str:
    """Nodo de estado (el mismo motivo de los 4 pasos) + texto."""
    out = []
    if live:
        out.append(f'<circle class="pulse" cx="{x + 6}" cy="{y - 5}" r="6" stroke="{t["accent"]}" stroke-width="1.5"/>')
    out.append(f'<circle cx="{x + 6}" cy="{y - 5}" r="4.5" fill="{t["accent"]}"/>')
    out.append(label(s, x + 20, y, t["accent_text"], 13))
    return "".join(out)


PULSE_CSS = (".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 3.2s ease-out infinite}"
             "@keyframes pulse{0%{transform:scale(1);opacity:.9}70%,100%{transform:scale(2.6);opacity:0}}")


def flow_css(length: float, period: float, dash: float = 110) -> str:
    return (f".flow{{stroke-dasharray:{dash} {_num(length + dash)};animation:flow {period}s linear infinite}}"
            f"@keyframes flow{{from{{stroke-dashoffset:{dash}}}to{{stroke-dashoffset:{_num(-length)}}}}}"
            ".lit{opacity:.28;animation:lit var(--p) ease-out infinite}"
            "@keyframes lit{0%{opacity:.28}6%{opacity:1}40%,100%{opacity:.28}}")


def lit_delay(at: float, period: float) -> str:
    """Retardo negativo para que el nodo se encienda cuando pasa el pulso."""
    return f"{_num(((at - 0.1) % period) - period)}s"


PIXEL = ROOT / "assets" / "pixel"


def scene(name: str, x: float, y: float, w: float, h: float, fit: str = "slice") -> str:
    """Escena pixel art (PNG nativo incrustado) escalada sin suavizado."""
    import pixel

    return (f'<image href="{pixel.png_data_uri(PIXEL / f"{name}.png")}" x="{_num(x)}" y="{_num(y)}" '
            f'width="{_num(w)}" height="{_num(h)}" preserveAspectRatio="xMidYMid {fit}" '
            f'style="image-rendering:crisp-edges;image-rendering:pixelated"/>')


def corners(w: float, h: float, o: float = 10, k: float = 14) -> str:
    return (f'<path d="M{o} {o + k}V{o}H{o + k}M{w - o - k} {o}H{w - o}V{o + k}M{w - o} {h - o - k}V{h - o}H{w - o - k}'
            f'M{o + k} {h - o}H{o}V{h - o - k}" stroke="#22C3D6" stroke-width="1.5" stroke-opacity=".7"/>')


def shadowed(face: "Face", s: str, x: float, y: float, size: float, fill: str, **kw) -> str:
    """Texto con sombra en escalón para escribir sobre escenas pixel."""
    return text(face, s, x + 3, y + 3, size, "#06121B", **kw) + text(face, s, x, y, size, fill, **kw)


def write(name: str, theme: str, content: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- contenido

STEPS = [
    ("01", "Entender", "Requerimientos, usuarios y qué significa que el proyecto salga bien."),
    ("02", "Diseñar", "Arquitectura, modelo de datos y alcance por fases."),
    ("03", "Construir", "Web y móvil, integraciones y pruebas automatizadas."),
    ("04", "Desplegar", "Puesta en producción, manuales y guía de operación."),
]

IMPACT = [
    ("12", "días de cero a producción"),
    ("+1.800", "pruebas automatizadas en un solo proyecto"),
    ("iOS + Android", "apps publicadas en App Store y Google Play"),
    ("5", "productos en producción o piloto"),
]

PROJECTS = [
    dict(
        slug="federacion",
        kind="Proyecto para cliente",
        status="En producción",
        title="FECODATLE · Federación Colombiana de Atletismo",
        what="Web y panel de gestión. La federación se había quedado sin sitio web.",
        result="En 12 días pasó a publicar sola noticias, documentos, calendario y galería desde su propio panel.",
        chips=["+1.800 pruebas", "Accesibilidad 100/100", "Acceso por roles"],
        stack="Next.js · TypeScript · PostgreSQL",
        art="proj-federacion",
    ),
    dict(
        slug="seguridad",
        kind="Proyecto para cliente",
        status="En operación",
        title="Plataforma B2B de seguridad y emergencias",
        what="App móvil, panel de administración web y backend en la nube.",
        result="En operación con clientes activos y app publicada en App Store y Google Play.",
        chips=["629 pruebas", "Entrega con acta", "Manuales de operación"],
        stack="React Native/Expo · Next.js · FastAPI · PostgreSQL",
    ),
    dict(
        slug="filo",
        kind="Producto Magnor",
        status="Piloto remunerado",
        title="Filo · SaaS para profesionales de la belleza",
        what="Web y app móvil, pensadas para Latinoamérica.",
        result="Ya está en pilotos remunerados.",
        chips=["176 pruebas", "73 endpoints", "29 tablas"],
        stack="Next.js · Expo · Drizzle · PostgreSQL",
        art="proj-filo",
    ),
    dict(
        slug="atencion-ia",
        kind="Producto Magnor",
        status=None,  # TODO: confirmar estado (producción / piloto)
        title="Atención al cliente con IA, multiempresa",
        what="Varias empresas en una sola plataforma, cada una con su propia base de conocimiento.",
        result="Búsqueda semántica conectada a Claude y panel de supervisión.",
        chips=["+1.000 pruebas", "Multiempresa", "Búsqueda semántica"],
        stack="Python · FastAPI · PostgreSQL · Next.js",
    ),
]

MAGNOR = dict(
    slug="magnor",
    kind="Producto Magnor",
    status="En producción",
    title="magnor.tech · sitio corporativo y software interno",
    what="Portada 3D y herramientas internas: Kanban, calendario y documentos.",
    result="En producción 15 días después de empezar.",
    chips=["171 pruebas", "15 días a producción", "Portada 3D"],
    stack="Next.js · React · PostgreSQL",
    art="proj-magnor",
)

STACK = [
    ("Interfaz web y móvil", ["React", "Next.js", "Tailwind", "React Native", "Expo"]),
    ("Backend y APIs", ["Node.js", "NestJS", "FastAPI", "REST", "Redis"]),
    ("Datos", ["PostgreSQL", "Supabase", "Firebase", "Drizzle"]),
    ("IA y machine learning", ["SDK de Anthropic", "AI SDK", "XGBoost"]),
    ("Integraciones", ["WhatsApp Business API", "Wompi", "Google APIs", "Twilio"]),
    ("Infra y despliegue", ["Docker", "GitHub Actions", "Google Cloud", "Vercel", "Cloudflare"]),
]
LANGUAGES = ["TypeScript", "JavaScript", "Python", "SQL"]

SECTIONS = {
    "proyectos": ("01", "Proyectos", "Casos de estudio"),
    "stack": ("02", "Stack", "Agrupado por capas"),
    "proceso": ("03", "Cómo trabajo", "De la idea a producción"),
    "actividad": ("04", "Actividad", "Generado a diario por GitHub Actions"),
}


# ---------------------------------------------------------------- piezas

def banner(t: dict) -> str:
    h, m = 400, 64
    period = 7.0
    b = [frame(t, 0, 0, W, h)]
    b.append(label("Bogotá, Colombia  ·  Software a medida y productos propios", m, 82, t["muted"], 14))
    b.append(label("4.711° N  74.072° W", W - m, 82, t["muted"], 14, anchor="end", w=400))
    b.append(text(SANS[700], "Jesús Nicolás Pachón Suárez", m, 160, 62, t["text"], track=-0.01))
    role = "Cofundador y COO de Magnor"
    b.append(text(MONO[500], role, m, 210, 24, t["accent_text"]))
    cx = m + MONO[500].width(role, 24) + 8
    b.append(f'<rect class="cur" x="{_num(cx)}" y="190" width="12" height="24" fill="{t["accent"]}"/>')
    b.append(f'<path d="M{m} 250H{W - m}" stroke="{t["border"]}" stroke-dasharray="2 6"/>')

    tag = "De la idea a producción."
    b.append(text(SANS[600], tag, m, 336, 34, t["text"]))
    x0 = m + SANS[600].width(tag, 34) + 56
    x1 = W - m - 52
    y = 325
    nodes = [x0 + (x1 - x0) * i / 3 for i in range(4)]
    length = x1 - x0
    b.append(f'<path d="M{_num(x0)} {y}H{_num(x1)}" stroke="{t["border"]}" stroke-width="2"/>')
    b.append(f'<path class="flow" d="M{_num(x0)} {y}H{_num(x1)}" stroke="{t["accent"]}" stroke-width="2" stroke-linecap="round"/>')
    for i, (nx, (num, name, _)) in enumerate(zip(nodes, STEPS)):
        at = period * (nx - x0) / length
        last = i == 3
        r = 9 if last else 7
        b.append(f'<circle cx="{_num(nx)}" cy="{y}" r="{r}" fill="{t["bg"]}" stroke="{t["accent"]}" stroke-width="2"/>')
        b.append(f'<circle class="lit" style="--p:{period}s;animation-delay:{lit_delay(at, period)}" '
                 f'cx="{_num(nx)}" cy="{y}" r="{r - 3.5}" fill="{t["accent"]}"/>')
        if last:
            b.append(f'<circle class="ring" style="animation-delay:{lit_delay(at, period)}" cx="{_num(nx)}" cy="{y}" '
                     f'r="{r}" stroke="{t["accent"]}" stroke-width="1.5"/>')
        b.append(label(f"{num} {name}", nx, y + 38, t["muted"], 12, anchor="middle"))
    css = (flow_css(length, period)
           + ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
           + f".ring{{transform-box:fill-box;transform-origin:center;opacity:0;animation:ring {period}s ease-out infinite}}"
           + "@keyframes ring{0%{transform:scale(1);opacity:.9}25%,100%{transform:scale(2.4);opacity:0}}")
    title = "Jesús Nicolás Pachón Suárez · Cofundador y COO de Magnor · De la idea a producción"
    return svg(W, h, title, "".join(b), css)


INTRO = ("Soy cofundador y COO de Magnor, una empresa de desarrollo de software con productos propios y "
         "proyectos a medida. Llevo proyectos de la idea a producción: requerimientos, arquitectura, desarrollo "
         "web y móvil, integraciones y despliegue. Estudio Ingeniería de Sistemas en la Universidad Jorge Tadeo "
         "Lozano (8.º semestre) y soy técnico en Electricidad y Electrónica.")
TYPE_CPS = 55  # caracteres por segundo del efecto de máquina de escribir


def intro(t: dict) -> str:
    """La intro como cuadro de diálogo de RPG: retrato, placa con el nombre y
    texto que se escribe una sola vez y queda fijo."""
    import pixel

    S = 4
    busts = [pixel.from_png(PIXEL / "portrait" / f"idle{i}.png") for i in range(2)]
    size, lh = 21, 31
    px0, py0 = 26, 46                       # esquina del cuadro (deja sitio a la placa)
    pw = 200                                # columna del retrato
    tx = px0 + pw + 40
    lines = SANS[400].wrap(INTRO, size, W - tx - 70)
    bh = max(len(lines) * lh + 64, 230)
    h = py0 + bh + 18
    box_w = W - 2 * px0
    bg = "#0B1E2B"

    b = [f'<rect x="{px0}" y="{py0}" width="{box_w}" height="{bh}" fill="{bg}"/>',
         # marco doble en escalón, como los cuadros de diálogo clásicos
         f'<rect x="{px0 + 3}" y="{py0 + 3}" width="{box_w - 6}" height="{bh - 6}" stroke="#E6F3F6" stroke-width="6" shape-rendering="crispEdges"/>',
         f'<rect x="{px0 + 12}" y="{py0 + 12}" width="{box_w - 24}" height="{bh - 24}" stroke="#22C3D6" stroke-width="3" shape-rendering="crispEdges"/>',
         f'<rect x="{px0 + 6}" y="{py0 + bh}" width="{box_w}" height="6" fill="#06121B"/>',
         f'<rect x="{px0 + box_w}" y="{py0 + 6}" width="6" height="{bh}" fill="#06121B"/>']

    # retrato
    fx, fy, fs = px0 + 34, py0 + 34, pw - 20
    b.append(f'<rect x="{fx}" y="{fy}" width="{fs}" height="{bh - 68}" fill="#10293A" stroke="#22C3D6" stroke-width="3" shape-rendering="crispEdges"/>')
    bw, bht = len(busts[0][0]) * S, len(busts[0]) * S
    ox, oy = fx + (fs - bw) / 2, fy + bh - 68 - bht
    b.append(f'<g shape-rendering="crispEdges"><g class="pb0">{pixel.to_paths(busts[0], S, ox, oy)}</g>'
             f'<g class="pb1">{pixel.to_paths(busts[1], S, ox, oy)}</g></g>')

    # placa con el nombre
    name = "JESÚS PACHÓN"
    nw = MONO[500].width(name, 15, 0.1) + 36
    b.append(f'<rect x="{px0 + 34}" y="{py0 - 18}" width="{_num(nw)}" height="40" fill="#06121B"/>'
             f'<rect x="{px0 + 30}" y="{py0 - 22}" width="{_num(nw)}" height="40" fill="#22C3D6"/>')
    b.append(text(MONO[500], name, px0 + 48, py0 + 4, 15, "#0B1E2B", track=0.1))

    # texto, con "Magnor" resaltado y una cortina por línea para el efecto de escritura
    css = []
    t0 = 0.6
    for i, line in enumerate(lines):
        y = py0 + 58 + i * lh
        k = line.find("Magnor")
        if k < 0:
            b.append(text(SANS[400], line, tx, y, size, "#E6F3F6"))
        else:
            pre, post = line[:k], line[k + 6:]
            b.append(text(SANS[400], pre, tx, y, size, "#E6F3F6"))
            b.append(text(SANS[400], "Magnor", tx + SANS[400].width(pre, size), y, size, "#22C3D6"))
            b.append(text(SANS[400], post, tx + SANS[400].width(pre + "Magnor", size), y, size, "#E6F3F6"))
        lw = SANS[400].width(line, size) + 12
        dur = len(line) / TYPE_CPS
        b.append(f'<rect class="tp" style="animation-duration:{dur:.2f}s;animation-delay:{t0:.2f}s;'
                 f'animation-timing-function:steps({len(line)})" x="{tx - 2}" y="{y - size - 4}" width="{_num(lw + 4)}" height="{lh}" fill="{bg}"/>')
        t0 += dur + 0.12
    b.append(f'<path class="nx" style="animation-delay:{t0:.2f}s" d="M{px0 + box_w - 56} {py0 + bh - 46}h18l-9 10z" fill="#22C3D6"/>')

    # la cortina se encoge hacia la derecha; sin animación queda a escala 0 (texto visible)
    css.append(".tp{transform-box:fill-box;transform-origin:100% 50%;transform:scaleX(0);animation-name:tp;animation-fill-mode:both}"
               "@keyframes tp{from{transform:scaleX(1)}to{transform:scaleX(0)}}")
    css.append(".nx{animation:nx 1s steps(1) infinite both}@keyframes nx{0%{opacity:1}50%{opacity:0}}")
    css.append(pixel.vis_css("pb1", [(3.2, 3.5)], 3.5) + ".pb0{opacity:1}")
    return svg(W, h, "Jesús Pachón: " + INTRO, "".join(b), "".join(css))


LINKS = [
    ("web", "SITIO WEB", "https://magnor.tech"),
    ("linkedin", "LINKEDIN", "https://www.linkedin.com/in/jesus-pachon-suarez"),
    ("email", "ESCRÍBEME", "mailto:pachonsuarezjesus@gmail.com"),
]


def menu_button(t: dict, label_text: str) -> str:
    """Botón de menú RPG: marco con esquinas en escalón, como las opciones de
    diálogo de un videojuego de 16 bits. Lleva un margen transparente a la
    derecha para que varios botones seguidos no queden pegados."""
    size, pad_x, h, gap = 15, 26, 52, 14
    tw = MONO[500].width(label_text, size, 0.08)
    w = round(tw + pad_x * 2 + 30)
    cut = 7  # tamaño del corte en escalón de cada esquina
    d = (f"M{cut} 0H{w - cut}L{w} {cut}V{h - cut}L{w - cut} {h}H{cut}L0 {h - cut}V{cut}Z")
    b = [f'<path d="{d}" fill="{t["bg"]}" stroke="#22C3D6" stroke-width="3" shape-rendering="crispEdges"/>']
    # flecha triangular, como el cursor de "continuar" del diálogo
    ay = h / 2
    b.append(f'<path d="M{pad_x - 14} {ay - 7}l12 7l-12 7z" fill="#22C3D6"/>')
    b.append(text(MONO[500], label_text, pad_x + 10, ay + size * 0.36, size, t["text"], track=0.08))
    return svg(w + gap, h, label_text, "".join(b))


def impact(t: dict) -> str:
    h, m = 200, 48
    vsize, lsize = 52, 17
    lw = 244  # ancho máximo de la etiqueta
    widths = [max(SANS[700].width(v, vsize), lw) for v, _ in IMPACT]
    gap = (W - 2 * m - sum(widths)) / (len(IMPACT) - 1)
    b = [frame(t, 0, 0, W, h, grid=False)]
    x = m
    for i, ((value, desc), cw) in enumerate(zip(IMPACT, widths)):
        b.append(text(SANS[700], value, x, 98, vsize, t["text"], track=-0.02))
        for j, line in enumerate(SANS[400].wrap(desc, lsize, lw)):
            b.append(text(SANS[400], line, x, 132 + j * 23, lsize, t["muted"]))
        b.append(f'<rect x="{_num(x)}" y="40" width="28" height="3" fill="{t["accent"]}"/>')
        if i < len(IMPACT) - 1:
            sx = x + cw + gap / 2
            b.append(f'<path d="M{_num(sx)} 44V160" stroke="{t["border"]}"/>')
        x += cw + gap
    title = "Impacto: " + " · ".join(f"{v} {d}" for v, d in IMPACT)
    return svg(W, h, title, "".join(b))


ART_H = 190       # alto del arte sobre las tarjetas de media anchura
SIDE_ART_W = 500  # ancho del arte a la derecha en la tarjeta ancha


def card_layout(p: dict, inner_w: float, pad: float, side: float = 0) -> dict:
    tw = inner_w - 2 * pad - side
    return dict(
        title=SANS[700].wrap(p["title"], 30, tw),
        what=SANS[400].wrap(p["what"], 18, tw),
        result=SANS[500].wrap(p["result"], 19, tw - 26),
        side=side,
        top=bool(p.get("art")) and not side,
    )


def card(t: dict, p: dict, w: float, h: float, lay: dict) -> str:
    o, pad = 8, 32  # margen exterior transparente (separa las tarjetas) y relleno interior
    iw, ih = w - 2 * o, h - 2 * o
    x0 = o + pad
    xr = w - o - pad - lay["side"]  # borde derecho del texto
    b = [frame(t, o, o, iw, ih, r=16)]
    if p.get("art"):
        b.append(f'<clipPath id="ca"><rect x="{o}" y="{o}" width="{iw}" height="{ih}" rx="16"/></clipPath>')
        if lay["side"]:
            ax = w - o - lay["side"]
            b.append(f'<g clip-path="url(#ca)">{scene(p["art"], ax, o, lay["side"], ih)}</g>')
            b.append(f'<path d="M{ax} {o}V{o + ih}" stroke="{t["border"]}"/>')
        else:
            b.append(f'<g clip-path="url(#ca)">{scene(p["art"], o, o, iw, ART_H)}</g>')
            b.append(f'<path d="M{o} {o + ART_H}H{o + iw}" stroke="{t["border"]}"/>')
        b.append(f'<rect x="{o + .5}" y="{o + .5}" width="{iw - 1}" height="{ih - 1}" rx="15.5" stroke="{t["border"]}"/>')
    y = o + (ART_H if lay["top"] else 0) + 50
    if p["status"]:
        b.append(status(t, p["status"], x0, y))
    b.append(label(p["kind"], xr, y, t["muted"], 12, anchor="end"))
    y += 52
    for line in lay["title"]:
        b.append(text(SANS[700], line, x0, y, 30, t["text"], track=-0.01))
        y += 37
    y += 10
    for line in lay["what"]:
        b.append(text(SANS[400], line, x0, y, 18, t["muted"]))
        y += 25
    y += 10
    b.append(text(SANS[500], "→", x0, y, 19, t["accent_text"]))
    for line in lay["result"]:
        b.append(text(SANS[500], line, x0 + 26, y, 19, t["text"]))
        y += 26
    cy = o + ih - 108
    cx = x0
    for c in p["chips"]:
        body, cw = chip(t, c, cx, cy, 13)
        if cx + cw > xr:
            break
        b.append(body)
        cx += cw + 8
    fy = o + ih - 52
    b.append(f'<path d="M{x0} {fy}H{xr}" stroke="{t["border"]}"/>')
    b.append(text(MONO[400], p["stack"], x0, fy + 30, 13, t["muted"]))
    b.append(label("Ver caso →", xr, fy + 30, t["accent_text"], 13, anchor="end"))
    title = f'{p["title"]}. {p["what"]} {p["result"]} Stack: {p["stack"]}.'
    return svg(w, h, title, "".join(b), PULSE_CSS if p["status"] else "")


def card_height(lay: dict) -> float:
    content = 50 + 52 + 37 * len(lay["title"]) + 10 + 25 * len(lay["what"]) + 10 + 26 * len(lay["result"])
    return content + 8 + 16 + 108 + 8 + (ART_H if lay["top"] else 0)  # chips + pie + márgenes (+ arte)


def section(t: dict, num: str, name: str, note: str) -> str:
    h = 64
    b = [label(num, 2, 40, t["accent_text"], 14), label(name, 40, 40, t["text"], 14)]
    nx = 40 + MONO[500].width(name.upper(), 14, 0.08) + 20
    note_w = MONO[400].width(note.upper(), 12, 0.08)
    b.append(f'<path d="M{_num(nx)} 35H{_num(W - note_w - 22)}" stroke="{t["border"]}"/>')
    b.append(label(note, W - 2, 40, t["muted"], 12, anchor="end", w=400))
    return svg(W, h, f"{num} {name}", "".join(b))


TREE_PERIOD = 8.0
TREE_EMIT = 5.3     # segundo del ciclo en que sale la onda
WAVE_SPEED = 650.0  # px/s


def stack(t: dict) -> str:
    """Stack por capas, como un edificio de pisos. Un árbol lanza una onda de
    sonido y cada tecnología tiembla al pasarle la onda, sin caerse."""
    import pixel

    m, row_h, top = 48, 66, 116
    h = top + row_h * len(STACK) + 30
    S = 3
    tree = {k: pixel.from_png(PIXEL / "tree" / f"{k}.png") for k in ("idle0", "idle1", "prep0", "blast0")}
    tw = max(len(g[0]) for g in tree.values()) * S
    th = max(len(g) for g in tree.values()) * S
    tx, ty = W - m - tw + 6, h - 22 - th          # esquina superior izquierda del árbol
    mouth_x, mouth_y = tx + 8, ty + th * 0.55      # boca (el árbol mira a la izquierda)

    def hit(cx: float) -> str:
        return f"{TREE_EMIT + max(mouth_x - cx, 0) / WAVE_SPEED:.2f}s"

    def quake(body: str, cx: float) -> str:
        return f'<g class="q" style="animation-delay:{hit(cx)}">{body}</g>'

    b = [frame(t, 0, 0, W, h, grid=False)]
    b.append(label("Lenguajes", m, 62, t["muted"], 12))
    x = m + 130
    for lang in LANGUAGES:
        lw = SANS[600].width(lang, 20)
        b.append(quake(text(SANS[600], lang, x, 64, 20, t["text"]), x + lw / 2))
        x += lw + 28
    spine = m + 6
    y0 = top + row_h / 2 - 4
    b.append(f'<path d="M{spine} {_num(y0)}V{_num(y0 + row_h * (len(STACK) - 1))}" stroke="{t["accent"]}" stroke-opacity=".45" stroke-width="1.5"/>')
    for i, (layer, items) in enumerate(STACK):
        ry = top + i * row_h
        cy = ry + row_h / 2 - 4
        b.append(f'<path d="M{m} {ry}H{tx - 20}" stroke="{t["border"]}"/>')
        b.append(f'<circle cx="{spine}" cy="{_num(cy)}" r="5" fill="{t["bg"]}" stroke="{t["accent"]}" stroke-width="1.5"/>')
        b.append(label(layer, m + 26, cy + 5, t["accent_text"], 13))
        x = m + 300
        for item in items:
            body, cw = chip(t, item, x, cy - 15, 14)
            b.append(quake(body, x + cw / 2))
            x += cw + 10

    # onda: tres arcos de bloques pixel que cruzan los pisos hacia la izquierda
    mid = top + row_h * len(STACK) / 2 - 4
    blocks = []
    for k, color in enumerate(("#E6F3F6", "#22C3D6", "#22C3D6")):
        R, span = 300 + k * 24, 210
        edge = (R * R - span * span) ** 0.5
        for yy in range(-span, span + 1, 6):
            xx = -((R * R - yy * yy) ** 0.5 - edge) - k * 24
            blocks.append(f'<rect x="{round(xx / 6) * 6}" y="{yy}" width="6" height="6" fill="{color}"/>')
    travel = mouth_x - (m + 260)
    b.append(f'<clipPath id="cw"><rect width="{W}" height="{h}" rx="18"/></clipPath>'
             f'<g clip-path="url(#cw)"><g transform="translate({_num(mouth_x)} {_num(mid)})">'
             f'<g class="wave" shape-rendering="crispEdges">{"".join(blocks)}</g></g></g>')

    # árbol (espejado para mirar a la izquierda)
    def sprite(k: str, cls: str) -> str:
        g = tree[k]
        gw, gh = len(g[0]) * S, len(g) * S
        ox = tx + (tw - gw) / 2
        oy = ty + th - gh
        return (f'<g class="{cls}" transform="translate({_num(ox + gw)} {_num(oy)}) scale(-1 1)">'
                f'{pixel.to_paths(g, S)}</g>')

    b.append(f'<rect x="{tx + 14}" y="{ty + th - 4}" width="{tw - 28}" height="8" rx="4" fill="#000" fill-opacity=".35"/>')
    b.append(f'<g shape-rendering="crispEdges"><g class="t-idle">{sprite("idle0", "ti0")}{sprite("idle1", "ti1")}</g>'
             f'{sprite("prep0", "t-prep")}{sprite("blast0", "t-blast")}</g>')

    P, e = TREE_PERIOD, TREE_EMIT
    end = e + travel / WAVE_SPEED
    css = [
        pixel.cycle_css("ti", 2, 0.5),
        pixel.vis_css("t-idle", [(0, e - 0.6), (e + 1.3, P)], P, base=1),
        pixel.vis_css("t-prep", [(e - 0.6, e)], P),
        pixel.vis_css("t-blast", [(e, e + 1.3)], P),
        f".wave{{opacity:0;animation:wave {P}s linear infinite}}"
        f"@keyframes wave{{0%,{100 * e / P:.2f}%{{transform:translateX(0);opacity:0}}"
        f"{100 * (e + 0.1) / P:.2f}%{{opacity:.95}}"
        f"{100 * (end - 0.15) / P:.2f}%{{opacity:.85}}"
        f"{100 * end / P:.2f}%{{transform:translateX(-{_num(travel)}px);opacity:0}}100%{{opacity:0}}}}",
        ".q{transform-box:fill-box;transform-origin:50% 100%;animation:quake " + f"{P}s linear infinite" + "}"
        "@keyframes quake{0%{transform:none}1.2%{transform:translate(-3px,0) rotate(-2deg)}"
        "2.4%{transform:translate(3px,-1px) rotate(1.6deg)}3.6%{transform:translate(-2px,0) rotate(-1deg)}"
        "4.8%{transform:translate(1px,0) rotate(.5deg)}6%,100%{transform:none}}",
    ]
    title = "Stack por capas. Lenguajes: " + ", ".join(LANGUAGES) + ". " + ". ".join(
        f"{layer}: {', '.join(items)}" for layer, items in STACK) + "."
    return svg(W, h, title, "".join(b), "".join(css))


def process(t: dict) -> str:
    """Nivel de videojuego con las 4 zonas; el texto va en el suelo."""
    h = 462
    ground = 334
    period = 8.0
    cols = [44, 334, 636, 928]
    col_w = 250
    b = [f'<clipPath id="c"><rect width="{W}" height="{h}" rx="18"/></clipPath><g clip-path="url(#c)">',
         scene("process", 0, 0, W, h),
         '<circle class="glow" cx="159" cy="186" r="46" fill="#F2E3A0"/>']
    x0, x1 = cols[0] + 6, cols[-1] + 6
    b.append(f'<path class="flow" d="M{x0} {ground}H{x1}" stroke="#22C3D6" stroke-width="3" stroke-linecap="square"/>')
    for (num, name, desc), cx in zip(STEPS, cols):
        at = period * (cx - cols[0]) / (x1 - x0)
        b.append(f'<rect x="{cx}" y="{ground - 6}" width="12" height="12" fill="#0B1E2B" stroke="#22C3D6" stroke-width="2"/>')
        b.append(f'<rect class="lit" style="--p:{period}s;animation-delay:{lit_delay(at, period)}" '
                 f'x="{cx + 3}" y="{ground - 3}" width="6" height="6" fill="#22C3D6"/>')
        b.append(label(num, cx, ground + 42, "#22C3D6", 13))
        b.append(text(SANS[600], name, cx + 30, ground + 43, 24, "#E6F3F6"))
        for j, line in enumerate(SANS[400].wrap(desc, 16, col_w)):
            b.append(text(SANS[400], line, cx, ground + 70 + j * 22, 16, "#8EA8B5"))
    b.append("</g>")
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="17.5" stroke="{t["border"]}"/>' + corners(W, h))
    css = (flow_css(x1 - x0, period) + ".glow{opacity:.1;animation:glow 3s ease-in-out infinite}"
           "@keyframes glow{50%{opacity:.28}}")
    title = "Cómo trabajo: " + " → ".join(f"{n}: {d}" for _, n, d in STEPS)
    return svg(W, h, title, "".join(b), css)


def cta(t: dict) -> str:
    """Cierre: Bogotá al amanecer, el cohete ya va en el cielo."""
    h, m = 489, 56
    b = [f'<clipPath id="c"><rect width="{W}" height="{h}" rx="18"/></clipPath><g clip-path="url(#c)">',
         scene("cta", 0, 0, W, h)]
    for i, (sx, sy) in enumerate([(612, 70), (700, 40), (540, 120), (880, 96), (980, 30), (430, 40)]):
        b.append(f'<rect class="tw" style="animation-delay:-{i * 0.7:.1f}s" x="{sx}" y="{sy}" width="3" height="3" fill="#9FE7F0"/>')
    b.append("</g>")
    b.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="17.5" stroke="{t["border"]}"/>' + corners(W, h))
    b.append(shadowed(MONO[500], "¿TIENES UN PROYECTO?", m, 74, 14, "#22C3D6", track=0.08))
    b.append(shadowed(SANS[700], "Lo llevamos de la idea", m, 132, 44, "#E6F3F6", track=-0.01))
    b.append(shadowed(SANS[700], "a producción.", m, 182, 44, "#E6F3F6", track=-0.01))
    b.append(shadowed(SANS[400], "Requerimientos, arquitectura, desarrollo web y móvil,", m, 224, 19, "#B9CFD8"))
    b.append(shadowed(SANS[400], "integraciones y despliegue.", m, 250, 19, "#B9CFD8"))
    bw, bh, by = 220, 56, 280
    b.append(f'<rect x="{m + 4}" y="{by + 4}" width="{bw}" height="{bh}" fill="#06121B"/>')
    b.append(f'<rect x="{m}" y="{by}" width="{bw}" height="{bh}" fill="#22C3D6"/>')
    b.append(text(SANS[600], "Escríbeme  →", m + bw / 2, by + bh / 2 + 7, 20, "#0B1E2B", anchor="middle"))
    b.append(label("Bogotá, Colombia  ·  Trabajo en remoto con clientes de cualquier país", m, h - 22, "#8EA8B5", 12, w=400))
    css = ".tw{opacity:.2;animation:tw 4.2s steps(1) infinite}@keyframes tw{0%{opacity:.2}50%{opacity:1}60%{opacity:.2}}"
    return svg(W, h, "¿Tienes un proyecto? Lo llevamos de la idea a producción. Escríbeme.", "".join(b), css)


STATS = [
    ("contributions", "contribuciones en 12 meses"),
    ("activeDays", "días con actividad"),
    ("longestStreak", "racha más larga, en días"),
    ("bestWeek", "contribuciones en la mejor semana"),
]
STATS_ART = 399  # alto de la escena de la oficina sobre las cifras
STATS_H, STATS_M, STATS_VSIZE = STATS_ART + 190, 48, 48


def stats_template(t: dict) -> tuple[str, list[dict]]:
    """Plantilla con marcadores; scripts/stats.mjs inserta las cifras."""
    col = (W - 2 * STATS_M) / len(STATS)
    top = STATS_ART
    b = [f'<clipPath id="c"><rect width="{W}" height="{STATS_H}" rx="18"/></clipPath><g clip-path="url(#c)">',
         f'<rect width="{W}" height="{STATS_H}" fill="{t["bg"]}"/>', scene("office", 0, 0, W, top),
         f'<path d="M0 {top}H{W}" stroke="#22C3D6" stroke-opacity=".5"/></g>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{STATS_H - 1}" rx="17.5" stroke="{t["border"]}"/>', corners(W, STATS_H)]
    slots = []
    for i, (key, desc) in enumerate(STATS):
        x = STATS_M + col * i
        b.append(f'<rect x="{_num(x)}" y="{top + 38}" width="28" height="3" fill="{t["accent"]}"/>')
        b.append(f"<!--{key}-->")
        slots.append(dict(key=key, x=round(x, 1), y=top + 96))
        b.append(text(SANS[400], desc, x, top + 128, 17, t["muted"]))
        if i:
            b.append(f'<path d="M{_num(x - 24)} {top + 42}V{top + 140}" stroke="{t["border"]}"/>')
    b.append("<!--updated-->")
    seal_svg, seal_css = seal(top)
    b.append(seal_svg)
    return svg(W, STATS_H, "__TITLE__", "".join(b), seal_css + "/*MOOD*/"), slots


SEAL_PERIOD = 6.0
SEAL_REST = 3.6   # segundos en reposo antes de cada acción
SEAL_X = 120      # bajo el escritorio, mirando hacia la ventana


def seal(floor: float) -> tuple[str, str]:
    """León marino en el suelo de la oficina. Su ánimo lo elige stats.mjs con
    los datos reales: celebra con la pelota en una gran semana, aplaude si hubo
    actividad reciente y saca la lengua, tranquilo, si no la hubo."""
    import pixel

    S = 3
    names ={"idle": 2, "clap": 3, "happy": 3, "blep": 3}
    grids = {f"{k}{i}": pixel.from_png(PIXEL / "seal" / f"{k}{i}.png") for k, n in names.items() for i in range(n)}
    sw = max(len(g[0]) for g in grids.values()) * S

    def frame_svg(key: str, cls: str) -> str:
        g = grids[key]
        gw, gh = len(g[0]) * S, len(g) * S
        return (f'<g class="{cls}" transform="translate({_num(SEAL_X + (sw - gw) / 2)} {_num(floor - 4 - gh)})">'
                f'{pixel.to_paths(g, S)}</g>')

    out = [f'<rect x="{SEAL_X + 24}" y="{floor - 8}" width="{sw - 40}" height="8" rx="4" fill="#000" fill-opacity=".4"/>',
           '<g shape-rendering="crispEdges">',
           f'<g class="sl-idle">{frame_svg("idle0", "si0")}{frame_svg("idle1", "si1")}</g>']
    for mood, n in (("clap", 3), ("happy", 3), ("blep", 3)):
        inner = "".join(frame_svg(f"{mood}{i}", f"s{mood[0]}{i}") for i in range(n))
        out.append(f'<g class="sl-act mood-{mood}">{inner}</g>')
    out.append("</g>")
    P, r = SEAL_PERIOD, SEAL_REST
    css = (pixel.cycle_css("si", 2, 0.9) + pixel.cycle_css("sc", 3, 0.36) + pixel.cycle_css("sh", 3, 0.6)
           + pixel.cycle_css("sb", 3, 0.75)
           + pixel.vis_css("sl-idle", [(0, r)], P, base=1) + pixel.vis_css("sl-act", [(r, P)], P)
           + ".mood-clap,.mood-happy,.mood-blep{display:none}")
    return "".join(out), css


def glyph_table(face: Face, chars: str, size: float) -> dict:
    return {c: dict(d=face.path(c, 0, 0, size), w=round(face.width(c, size), 2)) for c in chars}


def build_stats_templates() -> None:
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, t in THEMES.items():
        tpl, slots = stats_template(t)
        (TEMPLATES / f"stats-{name}.svg").write_text(tpl, encoding="utf-8")
        meta[name] = dict(text=t["text"], muted=t["muted"])
    meta["slots"] = slots
    meta["size"] = STATS_VSIZE
    meta["updated"] = dict(x=W - STATS_M, y=STATS_H - 26, size=12, prefix=label("Actualizado ", 0, 0, "#000", 12, w=400))
    meta["glyphs"] = glyph_table(SANS[700], "0123456789.", STATS_VSIZE)
    meta["mono"] = glyph_table(MONO[400], "0123456789-", 12)
    meta["prefix_w"] = round(MONO[400].width("ACTUALIZADO ", 12, 0.08), 2)
    (TEMPLATES / "stats.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- main

def main() -> None:
    card_w = 600
    layouts = [card_layout(p, card_w - 16, 32) for p in PROJECTS]
    card_h = max(card_height(l) for l in layouts)
    magnor_lay = card_layout(MAGNOR, W - 16, 32, side=SIDE_ART_W)
    magnor_h = card_height(magnor_lay)
    import build_pixel
    for name, t in THEMES.items():
        write("banner", name, build_pixel.banner(t))
        write("intro", name, intro(t))
        for key, label_text, _ in LINKS:
            write(f"btn-{key}", name, menu_button(t, label_text))
        write("impact", name, impact(t))
        for p, lay in zip(PROJECTS, layouts):
            write(f"card-{p['slug']}", name, card(t, p, card_w, card_h, lay))
        write("card-magnor", name, card(t, MAGNOR, W, magnor_h, magnor_lay))
        write("stack", name, stack(t))
        write("process", name, process(t))
        write("cta", name, cta(t))
        for key, (num, title, note) in SECTIONS.items():
            write(f"section-{key}", name, section(t, num, title, note))
    build_stats_templates()
    print(f"OK: {len(list(ASSETS.glob('*.svg')))} SVG en assets/")


if __name__ == "__main__":
    main()
