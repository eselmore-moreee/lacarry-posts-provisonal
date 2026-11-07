"""Controla el video final y saca fotogramas al azar del medio y del final."""
import argparse
import json
import random
import re
import subprocess
from pathlib import Path


def probar(*argumentos):
    return subprocess.run(["ffprobe", "-v", "error", *argumentos], capture_output=True, text=True, check=True).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--destino", default="video-ofertas/trabajo/verificacion")
    args = parser.parse_args()
    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    datos = json.loads(probar("-show_format", "-show_streams", "-of", "json", args.video))
    video = next(s for s in datos["streams"] if s["codec_type"] == "video")
    audio = next(s for s in datos["streams"] if s["codec_type"] == "audio")
    duracion = float(datos["format"]["duration"])

    claves = [float(v) for v in probar("-select_streams", "v", "-skip_frame", "nokey", "-show_entries", "frame=pts_time",
                                       "-of", "csv=p=0", args.video).replace(",", " ").split()]
    saltos = sorted({round(b - a, 3) for a, b in zip(claves, claves[1:])})

    medido = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", args.video, "-map", "0:a", "-af", "ebur128=peak=true",
                             "-f", "null", "-"], capture_output=True, text=True).stderr
    volumen = re.findall(r"I:\s+(-?[\d.]+) LUFS", medido)
    pico = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", medido)

    azar = random.Random(7)
    momentos = sorted([azar.uniform(duracion * .3, duracion * .7) for _ in range(5)]
                      + [azar.uniform(duracion * .9, duracion - 7) for _ in range(2)] + [duracion - 2.5])
    for i, momento in enumerate(momentos, 1):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{momento:.2f}", "-i", args.video, "-frames:v", "1",
                        str(destino / f"fotograma-{i}-{momento:.0f}s.png")], check=True)

    reporte = {
        "duracion_s": round(duracion, 2),
        "tamano_mb": round(int(datos["format"]["size"]) / 1048576, 1),
        "bitrate_kbps": round(int(datos["format"]["bit_rate"]) / 1000),
        "video": {k: video.get(k) for k in ("codec_name", "profile", "level", "pix_fmt", "width", "height", "r_frame_rate",
                                            "avg_frame_rate", "nb_frames", "color_space")},
        "audio": {k: audio.get(k) for k in ("codec_name", "channels", "sample_rate", "bit_rate", "duration")},
        "intervalos_entre_keyframes_s": saltos,
        "volumen_lufs": volumen[-1] if volumen else None,
        "pico_dbfs": pico[-1] if pico else None,
    }
    (destino / "reporte.json").write_text(json.dumps(reporte, indent=1, ensure_ascii=False), encoding="utf8")
    print(json.dumps(reporte, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
