#Buscar documentación sobre cómo funcionan operadores — jerarquía de búsqueda

No resolver de memoria. Según qué necesites, el orden correcto es:

### Operadores nativos de TD (TOP, CHOP, SOP, POP, COMP...)

Usar directamente `touchdesigner_docs_search_touchdesigner_docs` /
`touchdesigner_docs_get_full_touchdesigner_doc`. Es una capacidad nativa del
conector Tool Manager — **no** un operador del proyecto, no depende
del VFS ni de si hay LOPs instalado. Indexa docs.derivative.ca (parámetros
exactos, tipos, categorías, familias). Verificado con Noise TOP y con la
familia POP completa (build 2025.31550, incluye noisePOP con ~50 parámetros).

No hace falta `web_fetch` ni el repo para esto — es la vía más directa.

### Operadores LOPs (Agent, TTS, Tool Manager, Any, MCP Client...)

Tres pasos, en este orden:

1. **VFS del Tool Manager** — `file_tool_read_file("lops_architecture.md")`.
   Catálogo completo (88 operadores, categorizados: controllers, modifiers,
   pipelines, retrievers, settings) extraído de docs.dotsimulate.com.
   Más rápido que red y ya verificado que existe en el VFS.
1.2 **Mirar si hay documentación en el VFS** del Tool Manager:
```
file_tool_list_files(pattern="*")    ← SIEMPRE pattern="*" (sin él falla)
file_tool_read_file("nombre.md")     ← para leer cualquier archivo
```
⚠️ No buscar el operador tool_vfs1_virtualFile en la red — hay varias copias;
`file_tool_*` ya apunta al correcto.

3. Leer el documento que necesites de este router (tabla de abajo).

4. **No tocar producción.** Copiar operadores como `*_test`, usar modelos baratos.
3. **`web_fetch` a docs.dotsimulate.com** — si necesitas detalle que no está
   en el catálogo (parámetros exactos, ejemplos de uso). Usar fetch directo
   (urllib), no búsqueda site-scoped — ese sitio es JS-rendered y la
   búsqueda scopeada no es fiable.
4. **Este repo** — si es un pitfall, patrón o snippet ya documentado por una
   sesión anterior (ver `lops_pitfalls.md`, `lops_snippets.md`).

### Para gestionar archivos en el VFS del Tool Manager

| Tool | Para qué | Cuidado |
|---|---|---|
| `file_tool_list_files` | Listar archivos del VFS | Requiere `pattern="*"` (bug sin él) |
| `file_tool_read_file` | Leer archivo | Path = nombre del archivo directamente |
| `file_tool_write_file` | Escribir/crear archivo | Crea carpetas automáticamente |
| `file_tool_search_files` | Buscar texto en archivos | — |

### Leer un VFS externo (no el del Tool Manager)

`file_tool_*` solo ve el VFS interno del Tool Manager. Si el proyecto tiene
otro operador VFS (ej. en `/project1/alguna_carpeta/sd_tool_vfs1_virtualFile`),
léelo directamente con `td_code` o `network_context`:

```python
vfs_op = op('/project1/ruta/al/virtualFile')
for f in vfs_op.vfs:
    content = bytes(f.byteArray).decode('utf-8')
    print(f"=== {f.name} ===")
    print(content)
```

No hace falta añadir el operador al Tool Manager.
