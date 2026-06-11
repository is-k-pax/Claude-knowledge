# Como usar este repo

Instrucciones para humanos y para Claude.

**Ultima revision:** junio 2026.

---

## Para Claude

Al inicio de cualquier sesion tecnica:

1. Lee `router.md` de la raiz del repo via `github:get_file_contents`
   (owner: is-k-pax, repo: Claude-knowledge, path: router.md)
2. Segun la tabla del router, lee los documentos relevantes para la tarea
3. Si no encuentras lo que necesitas, díselo al usuario

Cuando descubras algo nuevo trabajando:
1. Identifica la categoria: pitfall, snippet, workflow, o conocimiento nuevo
2. Lee el documento correspondiente del repo ANTES de editarlo (nunca edites desde memoria)
3. Añade la seccion nueva siguiendo el formato existente
4. Commit con mensaje: `[carpeta] accion breve`
5. Cero datos personales — el repo es publico

Reglas operativas:
- Leer siempre la version actual antes de editar (otro Claude puede haberlo modificado)
- Si un commit falla por SHA mismatch, releer el archivo y reintentar
- Archivos < 10KB; si uno crece mas, proponer dividirlo al usuario
- Un archivo por commit (push_files falla con payloads grandes)

---

## Para humanos

El repo se organiza por programa (touchdesigner/, resolume/, etc.).
Cada carpeta tiene sus propios documentos modulares.

Para añadir contenido nuevo: abre una sesion con Claude, trabaja en el proyecto,
y al final de la sesion pide a Claude que commitee lo que ha aprendido.

Para consultar sin Claude: navega directamente por GitHub o usa las URLs raw
`https://raw.githubusercontent.com/is-k-pax/Claude-knowledge/main/<path>`
