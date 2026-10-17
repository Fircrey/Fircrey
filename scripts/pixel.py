"""Motor mínimo de pixel art: cuadrículas de color -> SVG nítido y animable.

Cada celda es un cuadrado de `scale` px. Las celdas contiguas del mismo color se
fusionan en una sola ruta por color, así que el SVG pesa poco y no tiene
antialiasing (shape-rendering: crispEdges).
"""

from __future__ import annotations

import random

Grid = list[list["str | None"]]


def new_grid(w: int, h: int, fill: "str | None" = None) -> Grid:
    return [[fill] * w for _ in range(h)]


def rect(g: Grid, x: int, y: int, w: int, h: int, color: "str | None") -> None:
    for yy in range(max(y, 0), min(y + h, len(g))):
        for xx in range(max(x, 0), min(x + w, len(g[0]))):
            g[yy][xx] = color


def stamp(g: Grid, rows: list[str], pal: dict[str, str], x: int, y: int) -> None:
    """Pega un sprite escrito en ASCII ('.' = transparente)."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != "." and ch in pal and 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = pal[ch]


def to_paths(g: Grid, scale: int, ox: float = 0, oy: float = 0) -> str:
    by_color: dict[str, list[str]] = {}
    for j, row in enumerate(g):
        i = 0
        while i < len(row):
            c = row[i]
            if c is None:
                i += 1
                continue
            k = i
            while k < len(row) and row[k] == c:
                k += 1
            by_color.setdefault(c, []).append(f"M{ox + i * scale} {oy + j * scale}h{(k - i) * scale}v{scale}h-{(k - i) * scale}z")
            i = k
    return "".join(f'<path fill="{c}" d="{"".join(d)}"/>' for c, d in by_color.items())


def sprite_svg(rows: list[str], pal: dict[str, str], scale: int, ox: float = 0, oy: float = 0) -> str:
    g = new_grid(max(len(r) for r in rows), len(rows))
    stamp(g, rows, pal, 0, 0)
    return to_paths(g, scale, ox, oy)


def scatter(g: Grid, rng: random.Random, n: int, box: tuple[int, int, int, int], color: str,
            avoid: tuple[int, int, int, int] | None = None) -> None:
    x0, y0, x1, y1 = box
    for _ in range(n):
        x, y = rng.randrange(x0, x1), rng.randrange(y0, y1)
        if avoid and avoid[0] <= x < avoid[2] and avoid[1] <= y < avoid[3]:
            continue
        if g[y][x] is not None:
            g[y][x] = color


def from_png(path) -> Grid:
    """Lee un PNG con transparencia como cuadrícula de colores hex (None = vacío)."""
    from PIL import Image

    im = Image.open(path).convert("RGBA")
    w, h = im.size
    data = im.load()
    return [[("#%02X%02X%02X" % data[x, y][:3]) if data[x, y][3] > 127 else None for x in range(w)] for y in range(h)]


def png_data_uri(path) -> str:
    import base64

    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
