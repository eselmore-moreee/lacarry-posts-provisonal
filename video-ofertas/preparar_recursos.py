"""Saca del fondo original de las cenefas los recursos livianos de video-ofertas/recursos.

Solo hace falta correrlo cuando cambia la campaña. Recibe una carpeta con el resultado de
`pdfimages -png -f 1 -l 1 cenefas.pdf im`: las primeras 5 imágenes son las tiras del fondo.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ORIGEN = Path(sys.argv[1])
DESTINO = Path(__file__).parent / "recursos"

# Recortes sobre la plantilla de 4016×2246 (x0, y0, x1, y1)
PIEZAS = {
    "sello-4anios": (2990, 30, 3960, 660),
    "globos": (3180, 1500, 4016, 2246),
    "cinta-dorada": (1955, 20, 2295, 335),
    "cinta-verde": (1640, 140, 1870, 355),
}
PAPEL = (1650, 380, 2930, 1100)


def plantilla():
    tiras = [Image.open(ORIGEN / f"im-{i:03d}.png").convert("RGB") for i in range(5)]
    lienzo = Image.new("RGB", (tiras[0].width, sum(t.height for t in tiras)))
    y = 0
    for tira in tiras:
        lienzo.paste(tira, (0, y))
        y += tira.height
    return lienzo


def recortar_sobre_papel(pieza, papel_rgb):
    """Vuelve transparente el papel conectado con el borde, sin tocar el interior de la pieza."""
    rgb = np.asarray(pieza, dtype=np.float32)
    papel = np.sqrt(((rgb - papel_rgb) ** 2).sum(axis=2)) < 42
    etiquetas, _ = ndi.label(papel)
    borde = np.unique(np.concatenate([etiquetas[0], etiquetas[-1], etiquetas[:, 0], etiquetas[:, -1]]))
    fondo = np.isin(etiquetas, borde[borde > 0])
    puro = np.sqrt(((rgb - papel_rgb) ** 2).sum(axis=2)) < 16
    puro[:, int(rgb.shape[1] * .5):] = False  # a la derecha del 4, ese tono es brillo de las letras
    huecos, _ = ndi.label(puro)
    tamanos = ndi.sum(puro, huecos, range(1, huecos.max() + 1))
    fondo |= ndi.binary_dilation(np.isin(huecos, np.flatnonzero(tamanos > 400) + 1), iterations=4)  # papel encerrado
    fondo = ndi.binary_dilation(fondo, iterations=2)
    partes, cantidad = ndi.label(~fondo)
    areas = ndi.sum(~fondo, partes, range(1, cantidad + 1))
    fondo |= np.isin(partes, np.flatnonzero(areas < 120) + 1)  # motas sueltas del papel
    alfa = ndi.gaussian_filter((~fondo).astype(np.float32), 1.0)
    return Image.fromarray(np.dstack([rgb, alfa * 255]).clip(0, 255).astype(np.uint8), "RGBA")


def main():
    base = plantilla()
    papel = base.crop(PAPEL)
    papel.save(DESTINO / "papel.jpg", quality=88)
    papel_rgb = np.median(np.asarray(papel).reshape(-1, 3), axis=0)
    for nombre, caja in PIEZAS.items():
        pieza = recortar_sobre_papel(base.crop(caja), papel_rgb)
        pieza = pieza.crop(pieza.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())
        pieza.thumbnail((760, 760), Image.LANCZOS)
        pieza.save(DESTINO / f"{nombre}.png", optimize=True)


if __name__ == "__main__":
    main()
