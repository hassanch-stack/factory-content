# Importación manual de contenido

## Decisión vigente

El paso 2 del flujo es una **importación manual**: el operador selecciona y
sube la foto que quiere procesar. El sistema no consulta, descarga ni crea
contenido desde fuentes externas de forma automática.

## Contrato

`POST /api/content/import` recibe `multipart/form-data` con:

- `file` (obligatorio): JPEG, PNG o WebP; se comprueba el binario real, no
  solo su extensión o el tipo que declara el navegador.
- `original_script` (obligatorio): texto o guion que el operador quiere
  reescribir. La IA no crea un guion desde cero.
- `title`, `category`, `language` (opcionales).
- `rights_status` (opcional; por defecto `UNKNOWN`).

La carga tiene un límite configurable con `MAX_UPLOAD_SIZE_BYTES` (20 MB
por defecto). La foto se guarda como `MediaAsset` original y el
`ContentItem` termina en estado `IMPORTED`, listo para el siguiente paso del
pipeline. El hash SHA-256 evita importar dos veces el mismo archivo.

## Garantías

- Se crea una fuente interna `MANUAL` solo para relacionar las cargas con el
  modelo de datos existente; no se hace polling sobre ella.
- Las fotos se guardan en el object storage, nunca como binario en la base de
  datos.
- Si falla la base de datos tras subir el archivo, se intenta eliminar el
  objeto almacenado.
- Subir un archivo personalmente no cambia la regla de derechos: contenido
  con `rights_status` no aceptable no puede pasar a publicación automática.

## Flujo posterior

1. El operador aporta el guion original durante la carga y abre el editor
   para reescribirlo o editarlo.
2. Selecciona una o más plantillas visuales en el orden del carrusel.
3. El primer render mueve el contenido de `IMPORTED` a `PROCESSING`.
4. Solo cuando terminan correctamente **todas** las diapositivas pasa a
   `READY_FOR_REVIEW`.
5. Tras revisión y derechos aceptables, se puede programar en una cuenta.

En producción, activar `AUTH_REQUIRED=true` exige enviar `AUTH_SECRET` como
Bearer token en todos los endpoints de negocio. La interfaz incluye una
pantalla de acceso para almacenar ese token solo en el navegador del
operador.
