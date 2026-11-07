#!/usr/bin/env bash
# Renderiza una composición HyperFrames a MP4 listo para Instagram (H.264 + audio AAC silencioso, 1080x1920).
# Uso: herramientas/render-video.sh <carpeta-con-index.html> <salida.mp4>
# La carpeta debe contener index.html y gsap.min.js (copiar plantillas/video-vertical/ como base).
# El logo (assets/logo.png) se copia a la carpeta si no está.
set -euo pipefail
DIR="$(cd "$1" && pwd)"
OUT="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export HYPERFRAMES_SKIP_SKILLS=1
export HYPERFRAMES_BROWSER_PATH="${HYPERFRAMES_BROWSER_PATH:-$(find /opt/pw-browsers -type f -name chrome | head -1)}"
[ -f "$DIR/logo.png" ] || cp "$REPO/assets/logo.png" "$DIR/logo.png"
[ -f "$DIR/gsap.min.js" ] || cp "$REPO/plantillas/video-vertical/gsap.min.js" "$DIR/gsap.min.js"
TMP="$DIR/_render.mp4"
(cd "$DIR" && npx --yes hyperframes@0.8.171 lint && npx --yes hyperframes@0.8.171 render . -o "$TMP" --quiet)
ffmpeg -v error -y -i "$TMP" -f lavfi -i anullsrc=r=44100:cl=stereo -c:v copy -c:a aac -shortest -movflags +faststart "$OUT"
rm -f "$TMP"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of default=nw=1 "$OUT"
