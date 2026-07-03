# MCP — Problemas comunes y soluciones

Troubleshooting de MCP transversal a todas las herramientas.

**Ultima revision:** julio 2026.

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

---

## tool_search solo devuelve un subconjunto de las tools de un servidor — no es cache desactualizada

**Sintoma:** un servidor MCP con muchas tools registradas (ej. 8 tools en un Tool Manager LOP) solo
muestra 4-5 de ellas al buscar. Reiniciar Claude Desktop no cambia nada. La lista visible varía
entre búsquedas dentro de la misma conversación, lo que parece un problema de cache o de conexión
intermitente.

**Causa real:** `tool_search` tiene un parámetro `limit` con valor por defecto **5**. Si un servidor
tiene más de 5 tools, solo se cargan las primeras 5 que matchean la query — el resto simplemente no
se piden, no es que fallen ni que estén cacheadas de una versión antigua.

**Fix:** pasar `limit` explícito, igual o mayor al número de tools del servidor:
```
tool_search(query="...", limit=20)
```

**Regla:** antes de diagnosticar un servidor MCP como roto, desconectado, o con cache corrupta
porque "faltan tools", comprobar primero si `tool_search` se llamó con `limit` por defecto (5).
No hace falta reiniciar Claude Desktop para este síntoma.
