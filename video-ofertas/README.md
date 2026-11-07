# Video de ofertas para las pantallas del súper

Genera el video de las teles (1280×720, 30 fps, H.264 High 4.0, AAC estéreo): portada, una oferta cada 5 s en el orden del PDF, mini-cortes "4 AÑOS" y cierre. El render corre en GitHub Actions, así no ocupa disco ni procesador de la PC. El video no entra al repo: queda como artifact del workflow durante 30 días.

## Regenerarlo

```bash
gh workflow run video-ofertas.yml -f version=normal -f modo=prueba
gh workflow run video-ofertas.yml -f version=normal -f modo=completo
```

- `prueba` deja en el artifact `revision` las hojas de contacto y los fotogramas de diseño.
- `completo` agrega `video` (el MP4) y `verificacion` (reporte y fotogramas al azar).

También se puede lanzar desde la pestaña Actions del repo, en "Video de ofertas". Para descargar el video:

```bash
gh run download <id-de-la-corrida> -n video
```

## Otra versión o el mes siguiente

Copiá `config/normal.json` y cambiá lo necesario; `version` es el nombre del archivo sin `.json`.

- `pdfs`: lista de PDFs en orden. Para la versión Carnicería, agregá su PDF después del general.
- `mes`, `vigencia`, `aclaracion`, `agradecimiento`: textos de portada y cierre.
- `minicorte_cada`: cada cuántas ofertas va el corte de 2 s (`0` lo desactiva).

Si cambia la campaña, `preparar_recursos.py` vuelve a sacar sello, globos, cintas y papel del fondo de las cenefas.

## Archivos

- `recortar.py`: rasteriza y detecta cada tarjeta.
- `render.py`: dibuja los fotogramas, codifica por tramos, une y agrega el audio.
- `musica.py`: sintetiza la pista lo-fi con numpy, sin material con derechos.
- `verificar.py`: controla el resultado con ffprobe.
- `recursos/`: arte recortado de las cenefas, logo y tipografía Barlow Condensed (licencia OFL).
