"""Convierte arte "tipo pixel art" generado por IA (JPEG, cuadrícula irregular)
en pixel art real: detecta el tamaño de celda, muestrea cada celda por su
centro, quita el fondo magenta y limita la paleta.

Es una herramienta de una sola vez: sus salidas (PNG pequeños a resolución
nativa) se guardan en assets/pixel/ y build_pixel.py las lee de ahí.

    pip install numpy scipy pillow
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.cluster.vq import kmeans2


def load(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def magenta_mask(img: np.ndarray) -> np.ndarray:
    """True donde hay fondo magenta (tolerante a artefactos JPEG)."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (np.minimum(r, b) - g > 70) & (r > 150) & (b > 150)


def period(img: np.ndarray, axis: int, lo: float = 4, hi: float = 20) -> tuple[float, float]:
    """Tamaño de celda y desfase a lo largo de un eje, por las fronteras de color."""
    lum = img.mean(axis=2)
    grad = np.abs(np.diff(lum, axis=1 - axis if axis == 0 else 0))
    sig = grad.sum(axis=0) if axis == 0 else grad.sum(axis=1)
    sig = sig - sig.mean()
    best = (0.0, lo, 0.0)
    for p in np.arange(lo, hi, 0.02):
        phase = 2 * np.pi * np.arange(len(sig)) / p
        c, s = (sig * np.cos(phase)).sum(), (sig * np.sin(phase)).sum()
        power = np.hypot(c, s) / len(sig)
        if power > best[0]:
            off = (np.arctan2(s, c) / (2 * np.pi) * p) % p
            best = (power, p, off)
    return best[1], best[2]


def sample(img: np.ndarray, mask: np.ndarray | None, cell: float, ox: float, oy: float):
    """Devuelve (colores HxWx3, alfa HxW) muestreando el centro de cada celda."""
    h, w = img.shape[:2]
    nx, ny = int((w - ox) // cell), int((h - oy) // cell)
    colors = np.zeros((ny, nx, 3), np.int16)
    alpha = np.zeros((ny, nx), bool)
    q = max(1, int(cell * 0.22))
    for j in range(ny):
        cy = int(oy + (j + 0.5) * cell)
        for i in range(nx):
            cx = int(ox + (i + 0.5) * cell)
            patch = img[cy - q:cy + q + 1, cx - q:cx + q + 1].reshape(-1, 3)
            if mask is not None:
                mp = mask[cy - q:cy + q + 1, cx - q:cx + q + 1].reshape(-1)
                if mp.mean() > 0.5:
                    continue
                patch = patch[~mp]
            colors[j, i] = np.median(patch, axis=0)
            alpha[j, i] = True
    return colors, alpha


def build_palette(samples: list[np.ndarray], k: int, seed: int = 7) -> np.ndarray:
    data = np.concatenate([s.reshape(-1, 3) for s in samples]).astype(float)
    centroids, _ = kmeans2(data, k, minit="++", seed=seed)
    return np.clip(np.round(centroids), 0, 255).astype(np.int16)


def quantize(colors: np.ndarray, palette: np.ndarray) -> np.ndarray:
    d = ((colors[..., None, :].astype(int) - palette[None, None].astype(int)) ** 2).sum(-1)
    return palette[d.argmin(-1)]


def save_rgba(colors: np.ndarray, alpha: np.ndarray, path: str) -> None:
    out = np.zeros(colors.shape[:2] + (4,), np.uint8)
    out[..., :3] = colors
    out[..., 3] = alpha * 255
    Image.fromarray(out, "RGBA").save(path, optimize=True)


def trim(colors: np.ndarray, alpha: np.ndarray, keep_largest: bool = True):
    """Recorta a la caja del sprite y quita motas sueltas."""
    if keep_largest:
        lab, n = ndimage.label(alpha)
        if n > 1:
            sizes = ndimage.sum(alpha, lab, range(1, n + 1))
            keep = [i + 1 for i, s in enumerate(sizes) if s >= max(6, sizes.max() * 0.02)]
            alpha = np.isin(lab, keep)
    ys, xs = np.nonzero(alpha)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return colors[y0:y1, x0:x1], alpha[y0:y1, x0:x1]
