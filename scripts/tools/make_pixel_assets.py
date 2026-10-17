"""Genera assets/pixel/ a partir de las imágenes de Gemini (una sola vez).

    python scripts/tools/make_pixel_assets.py --hero <hoja.jpg> --portrait <hoja.jpg> --tree <arbol.jpg> --seal <leon_marino.jpg>         --bg <bogota.jpg> --projects <proyectos.jpg> --process <niveles.jpg> --cta <amanecer.jpg> --office <oficina.jpg>

- Hojas de sprites (personaje, árbol, león marino): recorta cada fotograma,
  ajusta la cuadrícula (celda de 7,5 px), quita el fondo magenta y las
  etiquetas de texto, y unifica la paleta de cada hoja.
- Escenas de secciones: recorte + cuadrícula nativa + paleta limitada.
- Fondo: lo lleva a 400 px nativos, limita la paleta, borra las ventanas de
  código que quedarían bajo el texto y separa el cohete para animarlo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from pixelize import build_palette, load, magenta_mask, period, quantize, sample, save_rgba, trim

OUT = Path(__file__).resolve().parents[2] / "assets" / "pixel"

SHEET_CELL = 7.5
# fotogramas por hoja: (x0, y0, x1, y1) en la hoja original de 2400 x 1792
SHEETS = {
    "hero": dict(colors=22, frames={
        "walk": [(450, 372, 642, 792), (774, 372, 990, 792), (1098, 372, 1332, 792), (1446, 372, 1680, 792)],
        "type": [(558, 802, 996, 1238), (1074, 802, 1506, 1238), (1572, 802, 1998, 1238)],
        "bulb": [(642, 1260, 762, 1380)],
    }),
    "portrait": dict(colors=18, frames={  # misma hoja que "hero": bustos de reposo
        "idle": [(408, 48, 600, 360), (708, 48, 912, 360)],
    }),
    "tree": dict(colors=26, frames={
        "idle": [(216, 24, 552, 468), (594, 24, 936, 468)],
        "prep": [(1554, 30, 1914, 480)],
        "blast": [(630, 978, 948, 1386)],
    }),
    "seal": dict(colors=20, frames={
        "idle": [(90, 12, 600, 360), (642, 12, 1158, 360)],
        "clap": [(204, 360, 708, 720), (708, 360, 1200, 720), (1200, 360, 1680, 720)],
        "blep": [(168, 1062, 690, 1416), (696, 1062, 1206, 1416), (1218, 1062, 1734, 1416)],
        "happy": [(414, 1416, 912, 1788), (924, 1416, 1416, 1788), (1434, 1356, 1920, 1788)],
    }, exclude=[(0, 0, 276, 120), (0, 360, 276, 480), (0, 1062, 276, 1200), (0, 1416, 432, 1640), (1434, 1356, 1740, 1416)]),
}

BG_WIDTH = 400
# ventanas de código que quedarían bajo el texto (columnas y filas nativas, fin exclusivo)
BG_WINDOWS = [(341, 25, 358, 38), (116, 25, 140, 43), (82, 35, 110, 56), (244, 48, 263, 56), (33, 56, 51, 69)]
# zonas bajo el texto del banner: se borran las estrellas para que nada parezca un error
TEXT_ZONES = [(18, 19, 210, 28), (316, 19, 382, 28), (18, 32, 300, 53), (18, 57, 162, 68)]
# silueta del cohete: fila -> (col_ini, col_fin) inclusive
ROCKET_ORIGIN = (340, 100)
ROCKET_ROWS = {10: (22, 23), 11: (21, 24), **{r: (20, 25) for r in range(12, 31)}, **{r: (17, 28) for r in range(31, 33)},
               **{r: (17, 28) for r in range(33, 36)}, **{r: (16, 29) for r in range(36, 42)}}


# escenas: nombre -> (imagen fuente, recorte x0 y0 x1 y1 en px originales, celda nativa)
SCENES = {
    "proj-federacion": ("projects", (84, 6, 2400, 582), 6.0),
    "proj-filo": ("projects", (84, 606, 1800, 1194), 6.0),
    "proj-magnor": ("projects", (720, 1212, 1572, 1788), 6.0),
    "process": ("process", (0, 120, 3168, 1344), 7.92),
    "office": ("office", (0, 96, 3168, 1152), 7.92),
    "cta": ("cta", (0, 0, 3168, 1296), 7.92),
}


def scenes(sources: dict[str, str]) -> None:
    for name, (src, (x0, y0, x1, y1), cell) in SCENES.items():
        if src not in sources:
            continue
        crop = load(sources[src])[y0:y1, x0:x1]
        colors, _ = sample(crop, None, cell, 0, 0)
        q = quantize(colors, build_palette([colors], 40)).astype(np.uint8)
        Image.fromarray(q, "RGB").save(OUT / f"{name}.png", optimize=True)


def sheet(name: str, path: str) -> None:
    spec = SHEETS[name]
    img = load(path)
    mask = magenta_mask(img)
    for x0, y0, x1, y1 in spec.get("exclude", []):  # etiquetas de texto de la hoja
        mask[y0:y1, x0:x1] = True
    frames = {}
    for pose, boxes in spec["frames"].items():
        for k, (x0, y0, x1, y1) in enumerate(boxes):
            crop, m = img[y0:y1, x0:x1], mask[y0:y1, x0:x1]
            _, ox = period(crop, 0, SHEET_CELL - 0.05, SHEET_CELL + 0.06)
            _, oy = period(crop, 1, SHEET_CELL - 0.05, SHEET_CELL + 0.06)
            frames[f"{pose}{k}"] = trim(*sample(crop, m, SHEET_CELL, ox, oy))
    palette = build_palette([c[a] for c, a in frames.values()], spec["colors"])
    (OUT / name).mkdir(parents=True, exist_ok=True)
    for key, (colors, alpha) in frames.items():
        q = quantize(colors, palette).astype(int)
        r, g, b = q[..., 0], q[..., 1], q[..., 2]
        alpha = alpha & ~((b - g > 60) & (r > 25) & (r > g))  # restos morados del fondo
        save_rgba(q.astype(np.uint8), alpha, str(OUT / name / f"{key}.png"))


def background(path: str) -> None:
    img = load(path)
    cell = img.shape[1] / BG_WIDTH
    colors, _ = sample(img, None, cell, 0, 0)
    palette = build_palette([colors], 40)
    bg = quantize(colors, palette)

    for x0, y0, x1, y1 in BG_WINDOWS:  # relleno vertical entre el cielo de arriba y el de abajo
        top, bottom = bg[y0 - 1, x0:x1].astype(float), bg[y1, x0:x1].astype(float)
        for i, y in enumerate(range(y0, y1)):
            t = (i + 1) / (y1 - y0 + 1)
            bg[y, x0:x1] = np.round(top * (1 - t) + bottom * t)

    ox, oy = ROCKET_ORIGIN
    rocket_rows = [r + oy for r in ROCKET_ROWS]
    y_top, y_bot = min(rocket_rows), max(rocket_rows) + 1
    x_left = min(a for a, _ in ROCKET_ROWS.values()) + ox
    x_right = max(b for _, b in ROCKET_ROWS.values()) + ox + 1
    rocket = np.zeros((y_bot - y_top, x_right - x_left, 3), np.int16)
    alpha = np.zeros(rocket.shape[:2], bool)
    for r, (a, b) in ROCKET_ROWS.items():
        y, xa, xb = r + oy, a + ox, b + ox
        rocket[y - y_top, xa - x_left:xb - x_left + 1] = bg[y, xa:xb + 1]
        alpha[y - y_top, xa - x_left:xb - x_left + 1] = True
        # detrás del cohete: el color más frecuente de los 6 píxeles a su izquierda (evita copiar ventanas)
        near = [tuple(c) for c in bg[y, xa - 6:xa]]
        bg[y, xa:xb + 1] = max(set(near), key=near.count)

    lum = bg.sum(axis=2)
    local = ndimage.median_filter(lum, size=(3, 9))
    for x0, y0, x1, y1 in TEXT_ZONES:  # sólo puntos brillantes aislados (estrellas), no el resplandor
        for y in range(y0, y1):
            for x in range(x0, x1):
                if lum[y, x] > local[y, x] + 60:
                    bg[y, x] = bg[y, x - 3]

    bg = quantize(bg, palette)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(bg.astype(np.uint8), "RGB").save(OUT / "bg-bogota.png", optimize=True)
    save_rgba(rocket.astype(np.uint8), alpha, str(OUT / "rocket.png"))
    (OUT / "rocket.txt").write_text(f"{x_left} {y_top}\n", encoding="utf-8")  # posición en el fondo


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    for opt in ("hero", "portrait", "tree", "seal", "bg", "projects", "process", "cta", "office"):
        ap.add_argument(f"--{opt}")
    args = vars(ap.parse_args())
    OUT.mkdir(parents=True, exist_ok=True)
    for name in SHEETS:
        if args[name]:
            sheet(name, args[name])
    if args["bg"]:
        background(args["bg"])
    scenes({k: v for k, v in args.items() if v and k in {s for s, _, _ in SCENES.values()}})
    print("OK:", ", ".join(sorted(p.name for p in OUT.rglob("*.png"))))
