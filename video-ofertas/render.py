"""Arma el video de ofertas de las pantallas del súper.

Dibuja cada fotograma a 1280×720 con PIL, lo codifica por tramos y une todo con el concat
demuxer. La versión del video sale de config/*.json (fuentes, textos, cada cuánto va el mini-corte).

    python video-ofertas/render.py --config video-ofertas/config/normal.json --prueba
    python video-ofertas/render.py --config video-ofertas/config/normal.json
"""
import argparse
import json
import math
import multiprocessing
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ANCHO, ALTO = 1280, 720
FPS = 30
CUADROS_PORTADA = 6 * FPS
CUADROS_OFERTA = 5 * FPS
CUADROS_CORTE = 2 * FPS
CUADROS_CIERRE = 5 * FPS
ENTRADA = 12  # 0,4 s
SALIDA = 11

# Márgenes pensados para el recorte de bordes de una tele vieja
ANCHO_TARJETA = 1090
RADIO = 24

AQUI = Path(__file__).parent
RECURSOS = AQUI / "recursos"
FUENTE_FUERTE = RECURSOS / "BarlowCondensed-ExtraBold.ttf"
FUENTE_MEDIA = RECURSOS / "BarlowCondensed-SemiBold.ttf"

AZUL = (18, 58, 128)
AZUL_OSCURO = (11, 38, 92)
VERDE = (120, 190, 40)
TURQUESA = (10, 104, 112)
DORADO = (240, 180, 40)
ROJO = (226, 22, 30)
BLANCO = (255, 255, 255)
BEIGE = (246, 232, 208)
COLORES_CONFETI = [DORADO, (250, 208, 90), VERDE, (30, 136, 216), ROJO, BEIGE]

COMPARTE_ENCODE = [
    "-c:v", "libx264", "-preset", "veryfast", "-profile:v", "high", "-level", "4.0",
    "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
    "-r", str(FPS), "-g", str(2 * FPS), "-keyint_min", str(2 * FPS), "-sc_threshold", "0",
    "-b:v", "2200k", "-maxrate", "2500k", "-bufsize", "5000k", "-an", "-movflags", "+faststart",
]


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def salida_suave(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def rebote(x):
    """Escala con un pequeño pasado de largo, para las entradas con ritmo."""
    x = min(max(x, 0.0), 1.0)
    c = 1.4
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def con_alfa(capa, alfa):
    if alfa >= .999:
        return capa
    copia = capa.copy()
    copia.putalpha(capa.getchannel("A").point(lambda v: int(v * alfa)))
    return copia


def pegar(lienzo, capa, cx, cy, escala=1.0, alfa=1.0):
    """Pega una capa RGBA centrada en (cx, cy)."""
    if alfa <= .003 or escala <= .01:
        return
    if abs(escala - 1) > .002:
        capa = capa.resize((max(1, round(capa.width * escala)), max(1, round(capa.height * escala))), Image.BICUBIC)
    capa = con_alfa(capa, alfa)
    lienzo.paste(capa, (round(cx - capa.width / 2), round(cy - capa.height / 2)), capa)


def texto(contenido, ruta_fuente, tam, color, sombra=None, borde=0, color_borde=BLANCO):
    fuente = ImageFont.truetype(str(ruta_fuente), tam)
    margen = 24 + borde
    caja = fuente.getbbox(contenido, stroke_width=borde)
    capa = Image.new("RGBA", (caja[2] - caja[0] + margen * 2, caja[3] - caja[1] + margen * 2), (0, 0, 0, 0))
    posicion = (margen - caja[0], margen - caja[1])
    if sombra:
        base = Image.new("L", capa.size, 0)
        ImageDraw.Draw(base).text((posicion[0], posicion[1] + 5), contenido, font=fuente, fill=255, stroke_width=borde)
        difusa = base.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * sombra[3] / 255))
        capa.paste(Image.new("RGBA", capa.size, sombra[:3] + (255,)), (0, 0), difusa)
    ImageDraw.Draw(capa).text(posicion, contenido, font=fuente, fill=color + (255,), stroke_width=borde,
                              stroke_fill=color_borde + (255,))
    return capa


def texto_ajustado(contenido, ruta_fuente, ancho_max, tam_max, color, **opciones):
    tam = tam_max
    while ImageFont.truetype(str(ruta_fuente), tam).getlength(contenido) > ancho_max:
        tam -= 2
    return texto(contenido, ruta_fuente, tam, color, **opciones)


def destello_estrella(tam):
    """Destello dorado de cuatro puntas."""
    escala = 3
    lado = tam * escala
    capa = Image.new("L", (lado, lado), 0)
    d = ImageDraw.Draw(capa)
    c = lado / 2
    d.polygon([(c, 0), (c + lado * .045, c - lado * .045), (lado, c), (c + lado * .045, c + lado * .045),
               (c, lado), (c - lado * .045, c + lado * .045), (0, c), (c - lado * .045, c - lado * .045)], fill=255)
    capa = capa.filter(ImageFilter.GaussianBlur(escala)).resize((tam, tam), Image.LANCZOS)
    halo = Image.new("L", (tam, tam), 0)
    ImageDraw.Draw(halo).ellipse((tam * .3, tam * .3, tam * .7, tam * .7), fill=120)
    capa = ImageChops.lighter(capa, halo.filter(ImageFilter.GaussianBlur(tam / 10)))
    salida = Image.new("RGBA", (tam, tam), (255, 244, 200, 255))
    salida.putalpha(capa)
    return salida


def serpentina(lienzo, azar, x0, y0, dx, dy, onda, color, grosor):
    """Cinta enrulada, dibujada como la de la tarjeta, en un lienzo a escala 3."""
    d = ImageDraw.Draw(lienzo)
    pasos = 720
    fase = azar.uniform(0, 6.28)
    vueltas = azar.uniform(7, 10)
    for i in range(pasos):
        t = i / pasos
        giro = fase + t * vueltas
        x = x0 + dx * t + onda * math.sin(giro)
        y = y0 + dy * t + onda * .55 * math.cos(giro)
        luz = .72 + .4 * (math.cos(giro) * .5 + .5)
        r = grosor * (.55 + .45 * abs(math.cos(giro * .5)))
        tono = tuple(min(255, int(c * luz)) for c in color)
        d.ellipse((x - r, y - r, x + r, y + r), fill=tono + (255,))


def tarjeta_mascara(ancho, alto):
    mascara = Image.new("L", (ancho * 3, alto * 3), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, ancho * 3 - 1, alto * 3 - 1), RADIO * 3, fill=255)
    return mascara.resize((ancho, alto), Image.LANCZOS)


class Confeti:
    """Papelitos en función del cuadro global: cualquier tramo se puede dibujar por separado."""

    def __init__(self, cantidad, semilla, velocidad=1.0, tamanos=(8, 16)):
        azar = random.Random(semilla)
        self.piezas = []
        moldes = {}
        for _ in range(cantidad):
            color = azar.choice(COLORES_CONFETI)
            largo = azar.randint(*tamanos)
            clave = (color, largo)
            if clave not in moldes:
                moldes[clave] = self._giros(color, largo)
            self.piezas.append((moldes[clave], azar.uniform(0, ANCHO), azar.uniform(0, ALTO + 60),
                                azar.uniform(30, 62) * velocidad, azar.uniform(14, 34), azar.uniform(.3, .8),
                                azar.uniform(0, 6.28), azar.uniform(.5, 1.3)))

    @staticmethod
    def _giros(color, largo):
        ancho = max(3, int(largo * .5))
        lado = largo * 2
        giros = []
        for k in range(24):
            giro = k / 24 * 2 * math.pi
            alto = max(1, abs(math.cos(giro)) * ancho)
            lamina = Image.new("RGBA", (lado * 3, lado * 3), (0, 0, 0, 0))
            luz = .78 + .22 * abs(math.cos(giro))
            tono = tuple(int(c * luz) for c in color) + (235,)
            ImageDraw.Draw(lamina).rectangle((lado * 1.5 - largo * 1.5, lado * 1.5 - alto * 1.5,
                                              lado * 1.5 + largo * 1.5, lado * 1.5 + alto * 1.5), fill=tono)
            lamina = lamina.rotate(k * 15, Image.BICUBIC).resize((lado, lado), Image.LANCZOS)
            giros.append(lamina)
        return giros

    def dibujar(self, lienzo, cuadro):
        t = cuadro / FPS
        for giros, x0, y0, v, vaiven, ritmo, fase, rotacion in self.piezas:
            y = (y0 + v * t) % (ALTO + 60) - 30
            x = (x0 + vaiven * math.sin(ritmo * t + fase)) % ANCHO
            sprite = giros[int(rotacion * t * 12 + fase * 4) % 24]
            lienzo.paste(sprite, (int(x), int(y)), sprite)


class Fondo:
    """Degradado azul-verde que se mueve lento, con luces difusas y confeti."""

    def __init__(self):
        azar = np.random.default_rng(4)
        self.ruido = azar.integers(-2, 3, (ALTO, ANCHO, 1), dtype=np.int16)
        y, x = np.mgrid[0:36, 0:64].astype(np.float32)
        self.x, self.y = x / 63, y / 35
        self.confeti = Confeti(44, 11)
        self.luces = []
        generador = random.Random(5)
        for _ in range(7):
            lado = generador.randint(110, 230)
            luz = Image.new("L", (lado, lado), 0)
            ImageDraw.Draw(luz).ellipse((lado * .2, lado * .2, lado * .8, lado * .8), fill=generador.randint(26, 46))
            color = generador.choice([(255, 225, 150), (160, 225, 255), (190, 240, 150)])
            capa = Image.new("RGBA", (lado, lado), color + (0,))
            capa.putalpha(luz.filter(ImageFilter.GaussianBlur(lado / 10)))
            self.luces.append((capa, generador.uniform(0, ANCHO), generador.uniform(0, ALTO),
                               generador.uniform(.03, .07), generador.uniform(0, 6.28)))

    def dibujar(self, cuadro):
        t = cuadro / FPS
        cx1, cy1 = .5 + .42 * math.sin(t * .11), .45 + .35 * math.cos(t * .08)
        cx2, cy2 = .5 - .44 * math.cos(t * .07), .55 + .38 * math.sin(t * .13)
        mezcla1 = np.exp(-((self.x - cx1) ** 2 + (self.y - cy1) ** 2) * 4.2)[..., None]
        mezcla2 = np.exp(-((self.x - cx2) ** 2 + (self.y - cy2) ** 2) * 5.0)[..., None]
        rgb = (np.array(AZUL_OSCURO, np.float32) * (1 - mezcla1) + np.array(AZUL, np.float32) * 1.15 * mezcla1)
        rgb = rgb * (1 - mezcla2 * .75) + np.array(TURQUESA, np.float32) * mezcla2 * .75
        chico = Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")
        grande = np.asarray(chico.resize((ANCHO, ALTO), Image.BICUBIC), dtype=np.int16)
        lienzo = Image.fromarray((grande + self.ruido).clip(0, 255).astype(np.uint8), "RGB")
        for capa, x, y, velocidad, fase in self.luces:
            px = x + 90 * math.sin(t * velocidad + fase)
            py = y + 60 * math.cos(t * velocidad * 1.3 + fase)
            lienzo.paste(capa, (int(px - capa.width / 2), int(py - capa.height / 2)), capa)
        self.confeti.dibujar(lienzo, cuadro)
        return lienzo


class Recursos:
    def __init__(self, config):
        self.config = config
        cargar = lambda nombre: Image.open(RECURSOS / nombre).convert("RGBA")
        self.logo = cargar("logo.png")
        self.logo_chico = self.logo.resize((70, 70), Image.LANCZOS)
        self.sello = cargar("sello-4anios.png")
        self.globos = cargar("globos.png")
        self.cinta_dorada = cargar("cinta-dorada.png")
        self.cinta_verde = cargar("cinta-verde.png")
        self.papel = Image.open(RECURSOS / "papel.jpg").convert("RGB").resize((ANCHO, ALTO), Image.LANCZOS)
        self.fondo = Fondo()
        self.confeti_papel = Confeti(38, 21, velocidad=1.5, tamanos=(9, 18))
        self.estrella = destello_estrella(120)
        self.serpentinas = self._serpentinas()
        self.portada = self._capas_portada()
        self.cierre = self._capas_cierre()
        self.corte = self._capas_corte()

    def _serpentinas(self):
        azar = random.Random(8)
        escala = 2
        capa = Image.new("RGBA", (ANCHO * escala, ALTO * escala), (0, 0, 0, 0))
        for x0, y0, dx, dy, onda, color, grosor in [
            (-34, 740, 34, -780, 24, (24, 110, 200), 13),
            (1252, 740, 18, -300, 16, VERDE, 10),
            (690, -20, 240, 110, 34, VERDE, 11),
            (1040, -24, 280, 90, 30, (24, 110, 200), 12),
        ]:
            serpentina(capa, azar, x0 * escala, y0 * escala, dx * escala, dy * escala, onda * escala, color, grosor)
        return capa.resize((ANCHO, ALTO), Image.LANCZOS)

    def _capas_portada(self):
        azul = (16, 50, 118)
        c = {
            "linea1": texto("¡Bienvenidos a las", FUENTE_MEDIA, 86, azul),
            "linea2": texto("ofertas de", FUENTE_MEDIA, 86, azul),
            "mes": texto_ajustado(self.config["mes"] + "!", FUENTE_FUERTE, 660, 190, ROJO,
                                  sombra=(120, 40, 30, 120), borde=3),
            "grupo": texto("Grupo Avance", FUENTE_MEDIA, 50, azul),
            "logo": self.logo.resize((206, 206), Image.LANCZOS),
            "sello": self.sello.resize((540, round(540 * self.sello.height / self.sello.width)), Image.LANCZOS),
            "globos": self.globos.resize((318, round(318 * self.globos.height / self.globos.width)), Image.LANCZOS),
        }
        # Máscara del "4": es la mitad izquierda alta del sello
        sello = c["sello"]
        zona = Image.new("L", sello.size, 0)
        ImageDraw.Draw(zona).rectangle((0, 0, int(sello.width * .50), int(sello.height * .70)), fill=255)
        zona = zona.filter(ImageFilter.GaussianBlur(5))
        c["sello_cuatro"] = ImageChops.multiply(sello.getchannel("A"), zona)
        return c

    def _capas_cierre(self):
        azul = (16, 50, 118)
        return {
            "logo": self.logo.resize((262, 262), Image.LANCZOS),
            "gracias": texto(self.config["agradecimiento"], FUENTE_FUERTE, 104, ROJO, sombra=(120, 40, 30, 110)),
            "vigencia": texto_ajustado(self.config["vigencia"], FUENTE_MEDIA, 1040, 68, azul),
            "aclaracion": texto(self.config["aclaracion"], FUENTE_MEDIA, 38, azul),
            "sello": self.sello.resize((280, round(280 * self.sello.height / self.sello.width)), Image.LANCZOS),
            "globos": self.globos.resize((270, round(270 * self.globos.height / self.globos.width)), Image.LANCZOS),
        }

    def _capas_corte(self):
        lado = 900
        rayos = Image.new("L", (lado, lado), 0)
        d = ImageDraw.Draw(rayos)
        for k in range(18):
            a = k / 18 * 2 * math.pi
            d.polygon([(lado / 2, lado / 2),
                       (lado / 2 + lado * math.cos(a - .05), lado / 2 + lado * math.sin(a - .05)),
                       (lado / 2 + lado * math.cos(a + .05), lado / 2 + lado * math.sin(a + .05))], fill=70)
        centro = Image.new("L", (lado, lado), 0)
        ImageDraw.Draw(centro).ellipse((190, 190, lado - 190, lado - 190), fill=255)
        rayos = ImageChops.multiply(rayos.filter(ImageFilter.GaussianBlur(6)), centro.filter(ImageFilter.GaussianBlur(70)))
        capa = Image.new("RGBA", (lado, lado), (255, 222, 130, 0))
        capa.putalpha(rayos)
        return {
            "rayos": capa,
            "sello": self.sello.resize((720, round(720 * self.sello.height / self.sello.width)), Image.LANCZOS),
        }


class Tarjetas:
    def __init__(self, carpeta):
        self.archivos = sorted(Path(carpeta).glob("*.png"))
        if not self.archivos:
            sys.exit("No hay tarjetas: corré primero recortar.py")
        with Image.open(self.archivos[0]) as primera:
            self.alto = round(ANCHO_TARJETA * primera.height / primera.width)
        self.x = (ANCHO - ANCHO_TARJETA) // 2
        self.y = (ALTO - self.alto) // 2
        self.mascara = tarjeta_mascara(ANCHO_TARJETA, self.alto)
        margen = 40
        sombra = Image.new("L", (ANCHO_TARJETA + margen * 2, self.alto + margen * 2), 0)
        ImageDraw.Draw(sombra).rounded_rectangle((margen, margen + 6, margen + ANCHO_TARJETA, margen + self.alto + 6),
                                                 RADIO, fill=165)
        self.sombra = sombra.filter(ImageFilter.GaussianBlur(14))
        self.sombra_pos = (self.x - margen, self.y - margen)
        self.negro = Image.new("RGB", self.sombra.size, (4, 12, 32))

    def cargar(self, indice):
        with Image.open(self.archivos[indice]) as imagen:
            return imagen.convert("RGB").resize((ANCHO_TARJETA, self.alto), Image.LANCZOS)

    def dibujar(self, lienzo, tarjeta, escala, alfa):
        if alfa <= .003:
            return
        mascara_sombra = self.sombra if alfa >= .999 else self.sombra.point(lambda v: int(v * alfa))
        lienzo.paste(self.negro, self.sombra_pos, mascara_sombra)
        mascara = self.mascara
        x, y = self.x, self.y
        if abs(escala - 1) > .001:
            tam = (round(ANCHO_TARJETA * escala), round(self.alto * escala))
            tarjeta = tarjeta.resize(tam, Image.BILINEAR)
            mascara = mascara.resize(tam, Image.BILINEAR)
            x, y = (ANCHO - tam[0]) // 2, self.y + (self.alto - tam[1]) // 2
        if alfa < .999:
            mascara = mascara.point(lambda v: int(v * alfa))
        lienzo.paste(tarjeta, (x, y), mascara)


def poner_logo(lienzo, rec):
    lienzo.paste(rec.logo_chico, (24, 22), rec.logo_chico)


def escena_portada(rec, f, global_f):
    t = f / FPS
    c = rec.portada
    lienzo = rec.papel.copy()
    lienzo.paste(rec.serpentinas, (0, 0), rec.serpentinas)
    rec.confeti_papel.dibujar(lienzo, global_f)

    izquierda = 372
    aparece = lambda inicio, dura=.45: suave((t - inicio) / dura)
    desliza = lambda inicio: (1 - salida_suave((t - inicio) / .5)) * 46

    pegar(lienzo, rec.cinta_dorada, 1006 + 5 * math.sin(t * 1.3), 56, .28, aparece(.2))
    pegar(lienzo, rec.cinta_verde, 700 + 4 * math.sin(t * 1.1 + 1), 62, .24, aparece(.3))
    pegar(lienzo, c["logo"], izquierda - 214, 142, .55 + .45 * rebote((t - .1) / .6), aparece(.1, .3))
    pegar(lienzo, c["linea1"], izquierda - desliza(.7), 305, 1, aparece(.7))
    pegar(lienzo, c["linea2"], izquierda - desliza(1.05), 395, 1, aparece(1.05))
    pegar(lienzo, c["mes"], izquierda, 530, .7 + .3 * rebote((t - 1.45) / .55), aparece(1.45, .3))

    sube = (1 - salida_suave((t - .5) / 1.3)) * 280
    pegar(lienzo, c["globos"], ANCHO - c["globos"].width / 2 - 4, ALTO - c["globos"].height / 2 + sube + 6 * math.sin(t * 1.2),
          1, aparece(.5, .5))

    sello = c["sello"]
    sx, sy = 942, 268 + 5 * math.sin(t * 1.5)
    entrada = .55 + .45 * rebote((t - 1.95) / .6)
    pegar(lienzo, sello, sx, sy, entrada, aparece(1.95, .3))
    pegar(lienzo, c["grupo"], 866, 492, 1, aparece(2.5))

    if t > 2.5:
        for inicio, dura in ((2.6, .75), (4.1, .75)):
            avance = (t - inicio) / dura
            if 0 <= avance <= 1:
                banda = Image.new("L", sello.size, 0)
                centro = -80 + avance * (sello.width * .55 + 160)
                ImageDraw.Draw(banda).polygon([(centro - 34, sello.height), (centro + 34, sello.height),
                                               (centro + 140, 0), (centro + 72, 0)], fill=205)
                brillo = ImageChops.multiply(banda.filter(ImageFilter.GaussianBlur(8)), c["sello_cuatro"])
                x, y = round(sx - sello.width / 2), round(sy - sello.height / 2)
                lienzo.paste((255, 250, 225), (x, y, x + sello.width, y + sello.height), brillo)
        pulso = .5 + .5 * math.sin(t * 5.2)
        for dx, dy, tam, fase in ((-155, -104, .78, 0), (-72, -135, .5, 1.8), (-200, 12, .55, 3.2), (95, -82, .42, 4.4)):
            brillo = .5 + .5 * math.sin(t * 4.3 + fase)
            pegar(lienzo, rec.estrella, sx + dx, sy + dy, tam * (.6 + .4 * brillo), .35 + .65 * brillo * pulso)

    if f < 10:
        return Image.blend(rec.fondo.dibujar(global_f), lienzo, f / 10)
    restantes = CUADROS_PORTADA - f
    if restantes <= 12:
        return Image.blend(rec.fondo.dibujar(global_f), lienzo, (restantes - 1) / 12)
    return lienzo


def escena_cierre(rec, f, global_f):
    t = f / FPS
    c = rec.cierre
    lienzo = rec.papel.copy()
    lienzo.paste(rec.serpentinas, (0, 0), rec.serpentinas)
    rec.confeti_papel.dibujar(lienzo, global_f)
    aparece = lambda inicio, dura=.45: suave((t - inicio) / dura)

    pegar(lienzo, c["globos"], ANCHO - c["globos"].width / 2 - 4, ALTO - c["globos"].height / 2 + 5 * math.sin(t * 1.2),
          1, aparece(.3))
    pegar(lienzo, c["sello"], 1088, 118 + 4 * math.sin(t * 1.4), 1, aparece(.5))
    pegar(lienzo, c["logo"], 560, 178, .7 + .3 * rebote((t - .2) / .6), aparece(.2, .3))
    pegar(lienzo, c["gracias"], 560, 374 + (1 - salida_suave((t - .7) / .5)) * 26, 1, aparece(.7))
    pegar(lienzo, c["vigencia"], 560, 482 + (1 - salida_suave((t - 1.1) / .5)) * 26, 1, aparece(1.1))
    pegar(lienzo, c["aclaracion"], 560, 548, 1, aparece(1.5))

    if f < 12:
        return Image.blend(rec.fondo.dibujar(global_f), lienzo, f / 12)
    restantes = CUADROS_CIERRE - f
    if restantes <= 15:
        return Image.blend(Image.new("RGB", (ANCHO, ALTO)), lienzo, (restantes - 1) / 15)
    return lienzo


def escena_oferta(rec, tarjetas, tarjeta, f, global_f):
    lienzo = rec.fondo.dibujar(global_f)
    if f < ENTRADA:
        p = (f + 1) / ENTRADA
        tarjetas.dibujar(lienzo, tarjeta, .955 + .045 * salida_suave(p), suave(p))
    elif f >= CUADROS_OFERTA - SALIDA:
        tarjetas.dibujar(lienzo, tarjeta, 1, 1 - suave((f - (CUADROS_OFERTA - SALIDA) + 1) / SALIDA))
    else:
        tarjetas.dibujar(lienzo, tarjeta, 1, 1)
    poner_logo(lienzo, rec)
    return lienzo


def escena_corte(rec, f, global_f):
    t = f / FPS
    lienzo = rec.fondo.dibujar(global_f)
    alfa = suave(t / .3) * (1 - suave((f - CUADROS_CORTE + 10) / 10))
    c = rec.corte
    capa = c["rayos"].rotate(t * 16, Image.BILINEAR)
    pegar(lienzo, capa, ANCHO / 2, 340, 1, alfa)
    pegar(lienzo, c["sello"], ANCHO / 2, 340, .72 + .28 * rebote(t / .5), alfa)
    for dx, dy, tam, fase in ((-300, -130, 1.1, 0), (-130, -205, .7, 1.6), (272, -128, .85, 2.9), (330, 90, .6, 4.1), (-345, 88, .7, 5.1)):
        brillo = .5 + .5 * math.sin(t * 7 + fase)
        pegar(lienzo, rec.estrella, ANCHO / 2 + dx, 340 + dy, tam * (.6 + .4 * brillo), alfa * (.3 + .7 * brillo))
    poner_logo(lienzo, rec)
    return lienzo


def linea_de_tiempo(config, cantidad):
    """Lista de escenas [(tipo, índice, cuadro_inicial)] y su partición en tramos."""
    cada = config.get("minicorte_cada", 0)
    por_tramo = config.get("ofertas_por_tramo", 20)
    tramos, actual = [], [("portada", 0)]
    for i in range(cantidad):
        actual.append(("oferta", i))
        hecho = i + 1
        if cada and hecho % cada == 0 and hecho < cantidad:
            actual.append(("corte", i))
        if hecho % por_tramo == 0 and hecho < cantidad:
            tramos.append(actual)
            actual = []
    actual.append(("cierre", 0))
    tramos.append(actual)

    largos = {"portada": CUADROS_PORTADA, "oferta": CUADROS_OFERTA, "corte": CUADROS_CORTE, "cierre": CUADROS_CIERRE}
    cuadro = 0
    resultado = []
    for tramo in tramos:
        con_inicio = []
        for tipo, indice in tramo:
            con_inicio.append((tipo, indice, cuadro))
            cuadro += largos[tipo]
        resultado.append(con_inicio)
    return resultado, cuadro


def cuadros_de_escena(rec, tarjetas, escena):
    tipo, indice, inicio = escena
    if tipo == "portada":
        for f in range(CUADROS_PORTADA):
            yield escena_portada(rec, f, inicio + f)
    elif tipo == "cierre":
        for f in range(CUADROS_CIERRE):
            yield escena_cierre(rec, f, inicio + f)
    elif tipo == "corte":
        for f in range(CUADROS_CORTE):
            yield escena_corte(rec, f, inicio + f)
    else:
        tarjeta = tarjetas.cargar(indice)
        for f in range(CUADROS_OFERTA):
            yield escena_oferta(rec, tarjetas, tarjeta, f, inicio + f)


def renderizar_tramo(args):
    numero, tramo, config, carpeta_tarjetas, carpeta_tramos, hilos = args
    destino = Path(carpeta_tramos) / f"tramo{numero:03d}.mp4"
    if destino.exists():
        return str(destino)
    temporal = destino.with_suffix(".tmp.mp4")
    rec = Recursos(config)
    tarjetas = Tarjetas(carpeta_tarjetas)
    comando = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ANCHO}x{ALTO}",
               "-r", str(FPS), "-i", "-", *COMPARTE_ENCODE, "-threads", str(hilos), str(temporal)]
    proceso = subprocess.Popen(comando, stdin=subprocess.PIPE)
    for escena in tramo:
        for cuadro in cuadros_de_escena(rec, tarjetas, escena):
            proceso.stdin.write(cuadro.tobytes())
    proceso.stdin.close()
    if proceso.wait() != 0:
        raise RuntimeError(f"ffmpeg falló en el tramo {numero}")
    os.replace(temporal, destino)
    print(f"tramo {numero} listo", flush=True)
    return str(destino)


def prueba(config, carpeta_tarjetas, destino):
    """Fotogramas a tamaño real para validar el diseño antes del render largo."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    rec = Recursos(config)
    tarjetas = Tarjetas(carpeta_tarjetas)
    nombres = [a.stem for a in tarjetas.archivos]
    buscar = lambda sufijo: next(i for i, n in enumerate(nombres) if n.endswith(sufijo))
    for segundo in (.6, 1.7, 3.0, 4.4):
        f = int(segundo * FPS)
        escena_portada(rec, f, f).save(destino / f"portada-{segundo}.png")
    casos = {"comun": buscar("p02_1"), "kelloggs": buscar("p02_2"), "2x99": buscar("p02_3")}
    for nombre, i in casos.items():
        tarjeta = tarjetas.cargar(i)
        escena_oferta(rec, tarjetas, tarjeta, 75, 400 + 150 * i).save(destino / f"oferta-{nombre}.png")
    tarjeta = tarjetas.cargar(buscar("p02_2"))
    escena_oferta(rec, tarjetas, tarjeta, 5, 900).save(destino / "oferta-entrando.png")
    escena_corte(rec, 30, 3100).save(destino / "corte.png")
    escena_cierre(rec, 75, 40000).save(destino / "cierre.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--trabajo", default="video-ofertas/trabajo")
    parser.add_argument("--salida", default="video-ofertas/salida")
    parser.add_argument("--prueba", action="store_true")
    parser.add_argument("--procesos", type=int, default=os.cpu_count() or 2)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf8"))
    trabajo = Path(args.trabajo)
    carpeta_tarjetas = trabajo / "tarjetas"
    if args.prueba:
        prueba(config, carpeta_tarjetas, trabajo / "prueba")
        return

    carpeta_tramos = trabajo / "tramos"
    carpeta_tramos.mkdir(parents=True, exist_ok=True)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    cantidad = len(list(carpeta_tarjetas.glob("*.png")))
    tramos, cuadros = linea_de_tiempo(config, cantidad)
    duracion = cuadros / FPS
    print(f"{cantidad} ofertas, {len(tramos)} tramos, {cuadros} cuadros, {duracion:.1f} s", flush=True)

    tareas = [(i, t, config, str(carpeta_tarjetas), str(carpeta_tramos), 2) for i, t in enumerate(tramos)]
    with multiprocessing.Pool(args.procesos) as pool:
        archivos = pool.map(renderizar_tramo, tareas, chunksize=1)

    lista = trabajo / "tramos.txt"
    lista.write_text("".join(f"file '{Path(a).resolve().as_posix()}'\n" for a in archivos), encoding="utf8")
    solo_video = trabajo / "solo-video.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                    str(solo_video)], check=True)

    musica = trabajo / "musica.wav"
    subprocess.run([sys.executable, str(AQUI / "musica.py"), "--duracion", str(duracion), "--salida", str(musica)],
                   check=True)

    final = salida / f"{config['nombre']}.mp4"
    temporal = final.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(solo_video), "-i", str(musica), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-movflags", "+faststart", str(temporal)],
                   check=True)
    os.replace(temporal, final)
    print(final, flush=True)


if __name__ == "__main__":
    main()
