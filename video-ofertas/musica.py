"""Sintetiza una pista lo-fi propia (~75 bpm, sin voz, sin material con derechos).

Las colas de cada nota dan la vuelta al final del buffer, así que la unión del loop
queda fundida sola, sin corte. El loop dura ~8 minutos para que no se note la repetición.
"""
import argparse
import wave

import numpy as np
from scipy import signal

SR = 44100
BPM = 75
BEAT = 60 / BPM
COMPASES = 150
SEMILLA = 2026

# Séptimas y novenas en La menor / Do mayor, como (raíz MIDI, intervalos)
MAJ7, MIN7, DOM7, MIN9, MAJ9 = (0, 4, 7, 11), (0, 3, 7, 10), (0, 4, 7, 10), (0, 3, 7, 10, 14), (0, 4, 7, 11, 14)
SECCIONES = [
    [(57, MIN9), (53, MAJ7), (48, MAJ9), (55, DOM7)],
    [(53, MAJ9), (52, MIN7), (50, MIN9), (48, MAJ7)],
    [(50, MIN7), (55, DOM7), (48, MAJ9), (57, MIN7)],
    [(57, MIN7), (50, MIN9), (53, MAJ7), (52, MIN7)],
    [(48, MAJ7), (57, MIN9), (50, MIN7), (55, DOM7)],
]
PENTATONICA = [69, 72, 74, 76, 79, 81, 84]
ATAQUES = [(0, 2.5), (0, 1.5, 3), (.5, 2.5), (0, 2.75)]


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def sumar(buffer, nota, inicio, ganancia=1.0, paneo=0.5):
    """Mezcla circular: lo que se pasa del final entra por el principio del loop."""
    indices = (np.arange(len(nota)) + int(inicio * SR)) % len(buffer)
    np.add.at(buffer[:, 0], indices, nota * ganancia * np.cos(paneo * np.pi / 2))
    np.add.at(buffer[:, 1], indices, nota * ganancia * np.sin(paneo * np.pi / 2))


def piano(midi, duracion):
    t = np.arange(int(duracion * SR)) / SR
    f = hz(midi)
    tono = (np.sin(2 * np.pi * f * t) + .28 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3.5)
            + .09 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    return tono * np.exp(-t * 1.25) * np.minimum(t / .012, 1) * np.minimum((duracion - t) / .25, 1)


def colchon(midi, duracion):
    t = np.arange(int(duracion * SR)) / SR
    f = hz(midi)
    tono = np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * f * 1.003 * t) + .3 * np.sin(2 * np.pi * 2 * f * t)
    return tono * np.minimum(t / 1.1, 1) * np.minimum((duracion - t) / 1.4, 1)


def bajo(midi, duracion):
    t = np.arange(int(duracion * SR)) / SR
    f = hz(midi)
    tono = np.sin(2 * np.pi * f * t) + .22 * np.sin(2 * np.pi * 2 * f * t)
    return tono * np.exp(-t * 1.6) * np.minimum(t / .02, 1) * np.minimum((duracion - t) / .06, 1)


def bombo():
    t = np.arange(int(.34 * SR)) / SR
    fase = 2 * np.pi * np.cumsum(46 + 62 * np.exp(-t * 32)) / SR
    return np.sin(fase) * np.exp(-t * 11)


def filtrado(ruido, tipo, corte):
    return signal.sosfilt(signal.butter(2, corte, tipo, fs=SR, output="sos"), ruido, axis=0)


def poner_acorde(armonia, azar, inicio, raiz, intervalos):
    inversion = int(azar.integers(0, 2))
    alturas = [raiz + intervalo + (12 if i < inversion else 0) for i, intervalo in enumerate(intervalos)]
    for i, midi in enumerate(alturas):
        sumar(armonia, colchon(midi, 4 * BEAT + 1.2), inicio - .3, .042, .3 + .1 * i)
    for ataque in ATAQUES[int(azar.integers(0, len(ATAQUES)))]:
        for i, midi in enumerate(alturas):
            retraso = i * .013 + azar.uniform(0, .008)
            sumar(armonia, piano(midi, 2.6), inicio + ataque * BEAT + retraso, .085 * azar.uniform(.75, 1), .35 + .08 * i)


def poner_bajo(armonia, azar, inicio, raiz):
    base = raiz % 12 + 36
    for golpe, largo in [(0, 1.4), (1.5, .9), (2.5, 1.2)]:
        if golpe and azar.random() < .2:
            continue
        sumar(armonia, bajo(base, largo * BEAT + .1), inicio + golpe * BEAT, .23)
    if azar.random() < .5:
        sumar(armonia, bajo(base + 7, .55 * BEAT), inicio + 3.5 * BEAT, .17)


def poner_melodia(armonia, azar, inicio):
    paso = float(azar.choice([0, .5, 1, 2]))
    for _ in range(int(azar.integers(2, 5))):
        if paso >= 3.75:
            break
        tono = piano(int(azar.choice(PENTATONICA)), 1.8)
        sumar(armonia, tono, inicio + paso * BEAT, .075, .62)
        sumar(armonia, tono, inicio + (paso + .75) * BEAT, .022, .25)  # eco
        paso += float(azar.choice([.5, 1, 1.5]))


def poner_bateria(ritmo, azar, inicio, golpe_bombo, aro, plato):
    for golpe in (0, 2.5, 2.75) if azar.random() < .35 else (0, 2.5):
        sumar(ritmo, golpe_bombo, inicio + golpe * BEAT, .24)
    for golpe in (1, 3):
        sumar(ritmo, aro, inicio + golpe * BEAT + .012, .05, .45)
    for octavo in range(8):
        vaiven = .055 if octavo % 2 else 0  # swing
        fuerza = .021 if octavo % 2 else .032
        if azar.random() > .08:
            sumar(ritmo, plato, inicio + (octavo / 2) * BEAT + vaiven, fuerza * azar.uniform(.6, 1), .6)


def componer(azar):
    largo = int(COMPASES * 4 * BEAT * SR)
    armonia = np.zeros((largo, 2))
    ritmo = np.zeros((largo, 2))
    golpe_bombo = bombo()
    t_plato = np.arange(int(.07 * SR)) / SR
    t_aro = np.arange(int(.12 * SR)) / SR
    plato = filtrado(azar.standard_normal(len(t_plato)), "highpass", 7000) * np.exp(-t_plato * 90)
    aro = filtrado(azar.standard_normal(len(t_aro)), "bandpass", (900, 3200)) * np.exp(-t_aro * 38)

    compas = 0
    seccion = None
    while compas < COMPASES:
        seccion = int(azar.choice([s for s in range(len(SECCIONES)) if s != seccion]))
        con_bateria = azar.random() > .18  # algunos pasajes respiran sin batería
        for raiz, intervalos in SECCIONES[seccion] * int(azar.choice([1, 2])):
            if compas >= COMPASES:
                break
            inicio = compas * 4 * BEAT
            poner_acorde(armonia, azar, inicio, raiz, intervalos)
            poner_bajo(armonia, azar, inicio, raiz)
            if azar.random() < .42:
                poner_melodia(armonia, azar, inicio)
            if con_bateria:
                poner_bateria(ritmo, azar, inicio, golpe_bombo, aro, plato)
            compas += 1
    return armonia, ritmo


def circular(canal, sos):
    """Filtra sin marcar la unión del loop: procesa dos vueltas y se queda con la segunda."""
    return signal.sosfilt(sos, np.concatenate([canal, canal]))[len(canal):]


def masterizar(armonia, ritmo, azar):
    corte = signal.butter(2, 5200, "lowpass", fs=SR, output="sos")
    grave = signal.butter(1, 42, "highpass", fs=SR, output="sos")
    mezcla = np.column_stack([circular(armonia[:, 0], corte), circular(armonia[:, 1], corte)]) + ritmo
    izquierda, derecha = mezcla[:, 0].copy(), mezcla[:, 1].copy()
    mezcla[:, 1] += .16 * np.roll(izquierda, int(.023 * SR))
    mezcla[:, 0] += .16 * np.roll(derecha, int(.031 * SR))
    mezcla += filtrado(azar.standard_normal(mezcla.shape), "lowpass", 2400) * .0016  # siseo de vinilo
    mezcla = np.column_stack([circular(mezcla[:, 0], grave), circular(mezcla[:, 1], grave)])
    mezcla *= 10 ** (-20 / 20) / np.sqrt((mezcla ** 2).mean())
    return np.tanh(mezcla * 1.6) / 1.6


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duracion", type=float, required=True)
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()

    azar = np.random.default_rng(SEMILLA)
    loop = masterizar(*componer(azar), azar)
    muestras = int(round(args.duracion * SR))
    pista = loop[np.arange(muestras) % len(loop)]
    pista[:2 * SR] *= np.linspace(0, 1, 2 * SR)[:, None]
    pista[-6 * SR:] *= (np.linspace(1, 0, 6 * SR) ** 2)[:, None]

    with wave.open(args.salida, "wb") as salida:
        salida.setnchannels(2)
        salida.setsampwidth(2)
        salida.setframerate(SR)
        salida.writeframes((pista.clip(-1, 1) * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    main()
