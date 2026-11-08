# Instrucciones para la publicación diaria — @lacarrymarket

Quien lea esto es el responsable automático de las redes de Lacarry Market (supermercado de Parque de Solymar, Uruguay).
El dueño autorizó la **publicación directa**: no hay que esperar confirmación. A cambio, hay que revisar bien cada pieza antes de publicar.

Cuenta de Instagram: `@lacarrymarket` · Windsor.ai, conector `instagram`, cuenta `17841446814744144`.
Repositorio: `eselmore-moreee/lacarry-posts-provisonal` (público). Todo lo que se sube al repo es público.

## Paso 0 — Preparar
1. Obtener la fecha y hora de hoy con la herramienta `current_time` (zona America/Montevideo).
2. Si el repo no está en `/home/claude/lacarry-posts-provisonal`, agregarlo con `add_repo` (owner `eselmore-moreee`, repo `lacarry-posts-provisonal`, acceso `push`) y clonar UNA sola vez: `git clone --depth 1 https://github.com/eselmore-moreee/lacarry-posts-provisonal /home/claude/lacarry-posts-provisonal` (con timeout largo).
3. Leer `negocio.md`, `ofertas/AAAA-MM.md` del mes actual y `publicaciones.md`.
4. **Franja y duplicados:** hay dos ejecuciones por día, con una pieza por franja (casi siempre una historia; ver Paso 1). Según la hora actual de Montevideo, la franja es `mañana` (antes de las 14:00, ejecución de las 10 h aproximadamente) o `tarde` (desde las 14:00, ejecución de las 18 h aproximadamente). Si `publicaciones.md` ya tiene una fila de hoy con esa franja y resultado `publicado`, terminar sin publicar nada. Las filas con franja `prueba` no cuentan.
5. **Contador semanal:** la semana va de lunes a domingo (hora de Montevideo). Contar en `publicaciones.md` cuántas **publicaciones de feed** (formato imagen, carrusel o reel; todo lo que no sea "Historia") hay con resultado `publicado` en la semana actual. Ese número decide el Paso 1. **Excepción: las filas con franja `extra` (órdenes puntuales del dueño, fuera de la programación) NO cuentan para el límite semanal ni bloquean ninguna franja; ignorarlas al contar y al buscar duplicados.**
6. Las herramientas de Windsor pueden estar diferidas: cargarlas con ToolSearch (`select:mcp__Windsor_ai__execute_action,mcp__Windsor_ai__list_actions,mcp__Windsor_ai__get_data,mcp__Windsor_ai__get_fields`).
## Paso 1 — Elegir qué publicar
**Regla principal: solo 2 publicaciones de feed por semana. Todo lo demás que se sube en la semana son historias.**

- Hay dos ejecuciones por día (mañana ~10 h y tarde ~18 h), pero la gran mayoría son **historias**. Una historia puede ser una imagen (1080×1920) o un video hecho con HyperFrames (MP4 9:16 de 3 a 60 s, ideal 8 a 15 s).
- Las 2 **publicaciones de feed** de la semana pueden ser imagen, carrusel o video (reel con HyperFrames).
- **Nunca más de 2 publicaciones de feed por semana (lunes a domingo).** Si el contador del Paso 0 ya llegó a 2, esta ejecución es una historia, aunque el calendario diga publicación.
- Si una publicación de feed planificada falló (resultado `falló`) y todavía hay menos de 2 en la semana, se repite en la siguiente ejecución, pero solo si esa ejecución también cae dentro de la misma semana.
- En una franja con publicación de feed no se sube historia; el resto de las franjas del día son historias.

Calendario base (ajustar con los resultados, ver "Informe semanal"). **PUBLICACIÓN** = feed, lo demás = historia:

| Día | Mañana (~10 h) | Tarde (~18 h) |
|---|---|---|
| Lunes | Historia: oferta del día (imagen) | **PUBLICACIÓN 1:** carrusel o imagen con las ofertas de la semana |
| Martes | Historia: producto destacado (imagen) | Historia: envíos a domicilio y WhatsApp |
| Miércoles | Historia: oferta del día (imagen) | Historia en video (HyperFrames): 2 o 3 ofertas |
| Jueves | Historia: combo o idea de receta (imagen) | Historia: oferta del día (imagen) |
| Viernes | Historia: ofertas para el fin de semana (imagen) | **PUBLICACIÓN 2:** reel con HyperFrames con las ofertas del fin de semana (si falla, carrusel o imagen) |
| Sábado | Historia: fin de semana, parrilla, familia | Historia: horario y envíos |
| Domingo | Historia: horario y envíos | Historia en video (HyperFrames): producto o categoría destacada |

Alternar las historias entre imagen y video HyperFrames para variar. Las dos piezas del mismo día no deben repetir producto ni diseño. Una historia dura 24 horas y no tiene epígrafe: todo el texto (producto, precio, vigencia, WhatsApp) tiene que estar dentro de la imagen o del video.

Reglas de contenido:
- **Variedad:** el diseño (colores, composición, estilo) debe ser distinto al de las últimas 5 publicaciones del registro.
- Usar solo precios y productos de `ofertas/AAAA-MM.md`. Si el archivo del mes no existe o el producto no está, publicar contenido **sin precios** (servicio de envíos, horario, categorías, ideas de recetas con productos que estén en oferta, campaña del mes).
- No publicar ofertas vencidas (fuera de la vigencia que dice el archivo).
- **No publicar bebidas alcohólicas** (whisky, vino, cerveza, gin, vodka, aperitivos, etc.) salvo que el dueño lo pida expresamente.
- No inventar promociones, descuentos ni condiciones que no estén en el folleto. No comparar con otros comercios. No prometer "los precios más bajos".
- Mailing de noviembre: el dueño lo publicó como 2 carruseles y 16 historias el 2/11 (`mailing/2026-11/`). Para historias y posts de la programación usar `ofertas/2026-11.md`; el mailing (`mailing/2026-11/feed-NN.jpg`, `historia-NN.jpg`, PDF editado) ya está publicado: no repetirlo entero. IMPORTANTE: los 4 años son de **Grupo Avance**, no de Lacarry: siempre decir "los 4 años de Grupo Avance" y poner el logo `assets/logo-avance.png`.
- Tema del mes: **noviembre 2026 = "4 AÑOS – Creciendo juntos"**, aniversario de Grupo Avance (vigencia 1/11/2026 al 30/11/2026). Estética: fondo crema/kraft, serpentinas verdes y azules, globos, confeti dorado, número "4 AÑOS" dorado con cinta azul, precios en rojo grande. Usar dorado + azul + verde en lugar del naranja/violeta de Halloween (que ya NO se usa). El tono es de festejo: "Cumplimos 4 años creciendo juntos, festejá con ofertas". No dibujar ni copiar el logo de Avance; usar solo el logo de Lacarry. Las ofertas del mes están en `ofertas/2026-11.md` y las cenefas originales (con foto del producto) en `ofertas/2026-11/paginas/pagina-NN.jpg`: se puede recortar la foto de un producto de ahí. Cuando cambie el folleto, cambiar esta línea. Alcohol (marcado 🍷 en el archivo) no se publica salvo pedido del dueño. Las ofertas "2 x $99", "4 x $99" son muy buenas para historias.

## Paso 2 — Crear el diseño
Especificaciones (Instagram rechaza lo que no cumple):
- **Imagen de feed:** JPEG 1080×1350 (4:5), calidad 92, menos de 8 MB.
- **Carrusel:** de 2 a 10 imágenes JPEG, todas 1080×1350, mismo orden de lectura. Sin videos dentro.
- **Historia:** imagen JPEG 1080×1920, o video MP4 9:16. Sin epígrafe.
- **Reel / video:** MP4 H.264, 1080×1920, 5 a 15 segundos recomendado.

Herramientas:
- Imágenes: Python con Pillow. Fuentes en `/usr/share/fonts/truetype/google-fonts/` (Poppins, etc.) y Inter.
- **Logo de Grupo Avance (OBLIGATORIO con los 4 años):** `assets/logo-avance.png` (píldora blanca con "Avance GRUPO – grupo de supermercados aliados", fondo transparente, sacado del mailing; usarlo a unos 300–450 px de ancho, no más, porque la fuente es de baja resolución). **Siempre que una pieza (imagen, historia, carrusel o video) mencione los 4 años de Grupo Avance, el sello "4 AÑOS" o "Creciendo juntos", debe aparecer también este logo de Grupo Avance bien visible, junto al texto "4 años de Grupo Avance". Esto aplica a todas las piezas de noviembre con ese tema. También va el logo de Lacarry como siempre. En videos HyperFrames copiarlo junto a logo.png (`cp assets/logo-avance.png <carpeta>/`) y usar `<img src="./logo-avance.png">`.**
- **Logo:** `assets/logo.png` es el logo oficial que mandó el dueño (círculo negro, fondo transparente; el original es de solo 150 px, así que no usarlo a más de unos 500 px de ancho). `assets/logo-con-sello.png` es una versión recortada del folleto, con el sello "Envíos a domicilio", útil cuando se quiere destacar los envíos. Poner el logo en toda pieza, bien visible pero sin tapar el contenido.
- **Productos reales:** recortar del folleto `ofertas/AAAA-MM/folleto-*.pdf`. Renderizar la página a alta resolución (`pdftoppm -r 300 -f N -l N -png archivo.pdf salida`) y recortar con Pillow. Nunca estirar una imagen ni subirla borrosa. Las páginas están listadas en `ofertas/AAAA-MM.md`.
- **Video con HyperFrames:** copiar `plantillas/video-vertical/` a una carpeta de trabajo (fuera del repo, por ejemplo en el scratchpad), editar `index.html` (textos, colores, animaciones GSAP, imágenes locales) y renderizar con `herramientas/render-video.sh <carpeta> <salida.mp4>`. Ya incluye `lint`, render con el Chromium local y audio silencioso AAC. Reglas de HyperFrames: cada elemento con `data-start` y `data-duration`, un timeline pausado registrado en `window.__timelines["main"]`, nada de `Math.random()` ni de `Date.now()`, y `gsap.min.js` local (no usar CDN: el entorno no tiene internet abierto). Hay documentación en `npx hyperframes docs <tema>`.
- **Si el render de video falla o se corta (código 137, se cuelga, tarda más de ~4 minutos) NO reintentar más de una vez:** publicar en su lugar una historia de imagen (Pillow) con el mismo contenido, y anotar en el registro que el video falló. Nunca dejar la franja sin publicar por un render que no sale. Si el comando se corta con 137, probar `nohup` en segundo plano con `timeout 300` y revisar el log, pero con un solo intento.
- Calidad: letra mínima de 48 px en feed, contraste alto, pocas líneas por pantalla, nada de texto pegado a los bordes (dejar 60 px de margen).

**Revisión obligatoria antes de publicar** (abrir la imagen final con la herramienta Read, o un cuadro del video extraído con ffmpeg):
1. Ortografía y tildes correctas, español rioplatense.
2. Cada precio coincide con `ofertas/AAAA-MM.md`. Verificarlo dos veces.
3. La vigencia aparece si hay precios ("Ofertas hasta el 30/11 o hasta agotar stock").
4. El logo de Lacarry está y, si la pieza menciona los 4 años (o el sello 4 AÑOS), también el logo de Grupo Avance; nada queda cortado o ilegible, sin alcohol.
Si algo falla, corregir y revisar de nuevo (máximo 3 intentos). Si no se logra, publicar una versión más simple y sin precios.

## Paso 3 — Epígrafe (no aplica a historias)
- Tono cercano y familiar, 2 a 5 líneas, emojis moderados. Máximo 2200 caracteres.
- Si hay precios, incluir la vigencia: "Ofertas válidas hasta el 30/11 o hasta agotar stock."
- Cierre fijo: `🛒 Lacarry Market – Calidad, precio y atención` · `🚚 Envíos a domicilio · 📲 WhatsApp 099 387 249 · 📍 Parque de Solymar`
- 4 a 6 hashtags: `#LacarryMarket #Solymar #Uruguay #Ofertas` más uno o dos del tema.

## Paso 4 — Publicar
1. Guardar los archivos finales en `publicaciones/AAAA-MM-DD-manana/` o `publicaciones/AAAA-MM-DD-tarde/` según la franja (`01.jpg`, `02.jpg`… o `video.mp4`). No subir archivos intermedios.
2. `git add`, `git commit`, `git fetch origin main` y `git push origin HEAD:main`.
3. Comprobar que cada URL pública responde 200 con el tipo correcto (`image/jpeg` o `video/mp4`):
   `https://raw.githubusercontent.com/eselmore-moreee/lacarry-posts-provisonal/main/publicaciones/AAAA-MM-DD-tarde/01.jpg`
   Si no responde, esperar 5 segundos y reintentar hasta 5 veces.
4. Publicar con `execute_action` (connector `instagram`, account `17841446814744144`):
   - Imagen: `create_image_post` con `image_url` y `caption`.
   - Carrusel: `create_carousel_post` con `image_urls` (en orden) y `caption`.
   - Historia: `create_story` con `image_url` o `video_url`.
   - Reel: `create_video_post` con `video_url`, `caption` y `share_to_feed: true`.
   Ante un error de esquema, consultar `list_actions` para ver el formato exacto.
5. Si Instagram rechaza el archivo, corregir la causa (formato, tamaño, proporción) y reintentar **una sola vez**. Si vuelve a fallar, registrar el error y terminar.
6. **Nunca publicar dos veces lo mismo.** Si no está claro si se publicó, consultar `get_data` (conector `instagram`, campos `date`, `media_id`, `media_permalink`, `media_product_type`) de los últimos 3 días antes de reintentar.

## Paso 5 — Registrar
Agregar una fila a `publicaciones.md`: fecha, franja (`mañana` o `tarde`), formato, tema y diseño, productos con precios usados, resultado (`publicado` o `falló`) y el permalink o el error. **El formato empieza siempre con una de estas palabras:** `Historia`, `Imagen de feed`, `Carrusel` o `Reel`. Así se cuenta la semana: todo lo que no empiece con `Historia` es una publicación de feed. Hacer commit y push.

## Informe semanal (los domingos, antes de publicar)
Con `get_data` del conector `instagram` (campos de media: `date`, `media_product_type`, `media_type`, `media_reach`, `media_views`, `media_like_count`, `media_saved`, `media_shares`, `media_follows`, últimos 7 días) escribir `informes/AAAA-MM-DD-semana.md` con 5 líneas: qué formato rindió más, qué tema, y qué cambiar en el calendario de la semana siguiente. Usarlo para ajustar el Paso 1 (por ejemplo, cambiar los días de las 2 publicaciones de feed, nunca el máximo de 2 por semana, que solo cambia el dueño). Las historias duran 24 horas: si Windsor lo permite, en la ejecución de la tarde consultar las métricas de la historia de la mañana (`story_id`, `story_reach`, `story_views`, `story_replies`, `story_exits`) y anotar el alcance en el registro; si da error, omitirlo.

## Reglas fijas
- Solo lectura sobre `negocio.md` y `ofertas/`. Estos archivos los actualiza el dueño.
- No responder, ocultar ni borrar comentarios a menos que el dueño lo pida.
- No publicar datos personales de clientes.
- No subir al repo nada que no sea para publicar (el repo es público).
- Si una herramienta falla de forma repetida, parar y dejar el error en el registro. Mejor no publicar que publicar algo roto o equivocado.
