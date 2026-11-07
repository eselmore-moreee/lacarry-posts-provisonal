"""Rasteriza las cenefas y guarda cada tarjeta en su propio PNG, en orden (página, posición)."""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

DPI = 250  # la tarjeta ocupa media página: a 150 dpi quedaría más chica que en pantalla
MIN_LADO_PT = 150
ALTO_MINIATURA = 150


def detectar_tarjetas(pagina, minimo):
    """Devuelve las cajas de los rectángulos no blancos, de arriba a abajo y de izquierda a derecha."""
    rgb = np.asarray(pagina)
    no_blanco = rgb.min(axis=2) < 242
    etiquetas, _ = ndi.label(ndi.binary_closing(no_blanco, iterations=3))
    cajas = []
    for corte in ndi.find_objects(etiquetas):
        alto, ancho = corte[0].stop - corte[0].start, corte[1].stop - corte[1].start
        if ancho >= minimo and alto >= minimo:
            cajas.append((corte[1].start, corte[0].start, corte[1].stop, corte[0].stop))
    mitad = pagina.height / 2
    return sorted(cajas, key=lambda c: ((c[1] + c[3]) / 2 > mitad, c[0]))


def tiene_producto(tarjeta):
    """El panel blanco de la izquierda queda vacío cuando el espacio no lleva oferta."""
    ancho, alto = tarjeta.size
    panel = np.asarray(tarjeta.crop((int(ancho * .09), int(alto * .09), int(ancho * .40), int(alto * .88))))
    return (panel.min(axis=2) < 225).mean() > .02


def huella(tarjeta):
    return np.asarray(tarjeta.convert("L").resize((48, 27), Image.BILINEAR), dtype=np.int16)


def hojas_de_contacto(archivos, destino):
    columnas, filas = 7, 7
    ancho = int(ALTO_MINIATURA * 16 / 9)
    por_hoja = columnas * filas
    for hoja in range(0, len(archivos), por_hoja):
        lienzo = Image.new("RGB", (columnas * (ancho + 6), filas * (ALTO_MINIATURA + 6)), (40, 40, 48))
        dibujo = ImageDraw.Draw(lienzo)
        for k, archivo in enumerate(archivos[hoja:hoja + por_hoja]):
            x, y = (k % columnas) * (ancho + 6) + 3, (k // columnas) * (ALTO_MINIATURA + 6) + 3
            lienzo.paste(Image.open(archivo).resize((ancho, ALTO_MINIATURA), Image.BILINEAR), (x, y))
            dibujo.rectangle((x, y, x + 72, y + 13), fill=(0, 0, 0))
            dibujo.text((x + 2, y + 1), archivo.stem, fill=(255, 255, 0))
        lienzo.save(destino / f"contacto-{hoja // por_hoja + 1:02d}.jpg", quality=86)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--trabajo", default="video-ofertas/trabajo")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf8"))

    trabajo = Path(args.trabajo)
    paginas_dir, tarjetas_dir, contacto_dir = trabajo / "paginas", trabajo / "tarjetas", trabajo / "contacto"
    for carpeta in (paginas_dir, tarjetas_dir, contacto_dir):
        carpeta.mkdir(parents=True, exist_ok=True)

    minimo = int(MIN_LADO_PT * DPI / 72)
    numero = 0
    guardadas, omitidas, tamanos, huellas = [], [], [], []
    for orden, pdf in enumerate(config["pdfs"], 1):
        prefijo = paginas_dir / f"pdf{orden}"
        subprocess.run(["pdftoppm", "-r", str(DPI), "-png", pdf, str(prefijo)], check=True)
        for ruta in sorted(paginas_dir.glob(f"pdf{orden}-*.png")):
            nro_pagina = int(ruta.stem.rsplit("-", 1)[1])
            with Image.open(ruta) as abierta:
                pagina = abierta.convert("RGB")
            cajas = detectar_tarjetas(pagina, minimo)
            if len(cajas) != 4:
                print(f"AVISO {ruta.name}: {len(cajas)} tarjetas detectadas")
            for posicion, caja in enumerate(cajas, 1):
                tarjeta = pagina.crop((caja[0] + 1, caja[1] + 1, caja[2] - 1, caja[3] - 1))
                if not tiene_producto(tarjeta):
                    omitidas.append(f"pag{nro_pagina}-pos{posicion}")
                    continue
                numero += 1
                archivo = tarjetas_dir / f"{numero:03d}_p{nro_pagina:02d}_{posicion}.png"
                tarjeta.save(archivo)
                guardadas.append(archivo)
                tamanos.append(tarjeta.size)
                huellas.append(huella(tarjeta))
            ruta.unlink()

    matriz = np.stack(huellas)
    duplicadas = []
    for i in range(len(matriz) - 1):
        distancia = np.abs(matriz[i + 1:] - matriz[i]).mean(axis=(1, 2))
        duplicadas += [(guardadas[i].stem, guardadas[i + 1 + j].stem, round(float(distancia[j]), 2))
                       for j in np.flatnonzero(distancia < 1.5)]
    relaciones = sorted({round(a / h, 2) for a, h in tamanos})
    reporte = {"tarjetas": len(guardadas), "espacios_omitidos": omitidas, "posibles_duplicadas": duplicadas,
               "relaciones_de_aspecto": relaciones, "tamanos": sorted(set(tamanos))}
    (trabajo / "tarjetas.json").write_text(json.dumps(reporte, indent=1, ensure_ascii=False), encoding="utf8")
    print(json.dumps(reporte, ensure_ascii=False))
    hojas_de_contacto(guardadas, contacto_dir)


if __name__ == "__main__":
    main()
