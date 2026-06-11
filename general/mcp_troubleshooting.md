# MCP — Problemas comunes y soluciones

Troubleshooting de MCP transversal a todas las herramientas.

**Ultima revision:** junio 2026.

---

## Timeout tras uso prolongado

**Sintoma:** las llamadas MCP fallan silenciosamente despues de mucho rato.
**Causa:** el proceso npx que corre el MCP server se cuelga.
**Fix:** reiniciar Claude Desktop completamente (cerrar + reabrir, no solo la ventana).

---

## web_fetch trunca archivos grandes

**Sintoma:** el contenido leido con web_fetch de una URL raw de GitHub se corta sin aviso.
**Causa:** web_fetch trunca silenciosamente por encima de ~8-10KB.
**Fix:** usar GitHub MCP (github:get_file_contents) en vez de web_fetch para archivos del repo.

---

## SHA mismatch al editar un archivo

**Sintoma:** github:create_or_update_file falla con "SHA does not match".
**Causa:** otro commit modifico el archivo desde que lo leiste. El SHA que enviaste ya no es el actual.
**Fix:** volver a leer el archivo con github:get_file_contents, obtener el SHA nuevo, y reintentar.

---

## push_files falla con payloads grandes

**Sintoma:** github:push_files da error o timeout al subir varios archivos a la vez.
**Causa:** el payload combinado es demasiado grande para una sola llamada.
**Fix:** usar github:create_or_update_file un archivo por commit.

---

## El MCP no conecta al arrancar Claude Desktop

**Sintoma:** las herramientas del MCP no aparecen o dan error al usarlas.
**Causa:** configuracion incorrecta en claude_desktop_config.json o token expirado.
**Fix:** verificar que el JSON es valido, que el token tiene scope "repo", y reiniciar Claude Desktop.
