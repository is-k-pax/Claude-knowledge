# LOPs — Router

LOPs (Language Operator Pack) = operadores de dotsimulate para construir
aplicaciones LLM dentro de TouchDesigner. No los conoces de entrenamiento.
Doc oficial: https://docs.dotsimulate.com/

---

## Al entrar a un proyecto TD con LOPs — hazlo en este orden

1. **Smoke test** — verificar conexión:
```python
# Desde network_context o td_code:
print(f"FPS: {project.cookRate}")
print(f"Ops en /project1: {len(op('/project1').children)}")
```

2. **Mirar si hay documentación en el VFS** del Tool Manager:
```
file_tool_list_files(pattern="*")    ← SIEMPRE pattern="*" (sin él falla)
file_tool_read_file("nombre.md")     ← para leer cualquier archivo
```
⚠️ No buscar el operador tool_vfs1_virtualFile en la red — hay varias copias;
`file_tool_*` ya apunta al correcto.

3. Leer el documento que necesites de este router (tabla de abajo).

4. **No tocar producción.** Copiar operadores como `*_test`, usar modelos baratos.

---

## Documentación — jerarquía de búsqueda

No resolver de memoria. Según qué necesites, el orden correcto es:

### Operadores nativos de TD (TOP, CHOP, SOP, POP, COMP...)

Usar directamente `touchdesigner_docs_search_touchdesigner_docs` /
`touchdesigner_docs_get_full_touchdesigner_doc`. Es una capacidad nativa del
conector `touchdesigner-lop` — **no** un operador del proyecto, no depende
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
2. **`web_fetch` a docs.dotsimulate.com** — si necesitas detalle que no está
   en el catálogo (parámetros exactos, ejemplos de uso). Usar fetch directo
   (urllib), no búsqueda site-scoped — ese sitio es JS-rendered y la
   búsqueda scopeada no es fiable.
3. **Este repo** — si es un pitfall, patrón o snippet ya documentado por una
   sesión anterior (ver `lops_pitfalls.md`, `lops_snippets.md`).

### Patrones, pitfalls, snippets ya conocidos

Repo `is-k-pax/Claude-knowledge` — ver tabla "Qué documento leer" más abajo.

---

## Tools del Tool Manager — las que usarás para trabajar

El Tool Manager expone ~25 tools via MCP (puerto 18766).
Estas son las que necesitas conocer, por orden de uso:

### Para construir y diagnosticar (las más usadas)

| Tool | Para qué | Cuidado |
|---|---|---|
| `network_context` | Python que **persiste** — crear ops, conectar, modificar la red real | Usar para cambios estructurales |
| `td_code` | Python en **sandbox** — inspeccionar, leer, probar | Cambios NO persisten entre calls |
| `td_mod` | Módulos curados: `catalog` (tipos de op), `net` (leer red), `search` (descubrir módulos) | action: list/doc/source/call |
| `edit_td_dat_*` | Editar DATs con precisión | Flujo: set_target → read_content → insert/str_replace |
| `ls` | Listar hijos de un COMP | Sin path = raíz del proyecto |
| `read` | Leer archivo o DAT con números de línea | Usar view_range para archivos grandes |
| `capture_network_screenshot` | Screenshot de la red | Requiere Pillow en el venv |
| `get_recent_activity` | Ver qué ha tocado el usuario recientemente | — |

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

### Otras disponibles

| Tool | Para qué |
|---|---|
| `str_replace`, `insert`, `create`, `undo` | Editar DATs y archivos, navegar |
| `search_web` | Búsqueda web via Serper (requiere API key) |

---

## Diferencia clave: network_context vs td_code

- **`network_context`**: Python con acceso completo al proyecto. Los operadores que
  crees, las conexiones que hagas, los parámetros que cambies → **persisten en la red real de TD**.
  Usar para cualquier cambio que deba quedarse.

- **`td_code`**: Python en sandbox aislado. Variables y operadores creados aquí
  **desaparecen al terminar el call**. Usar para inspección, lectura, pruebas rápidas.

Si te piden "crea un operador" o "conecta X con Y" → `network_context`.
Si te piden "mira qué hay en X" o "comprueba el valor de Y" → cualquiera de los dos vale.

---

## Qué documento leer según la situación

| Situación | Lee |
|---|---|
| Qué operadores LOPs existen y para qué | lops_catalog.md |
| Algo falla en LOPs o Tool Manager | lops_pitfalls.md |
| Código LOPs reutilizable (snippets) | lops_snippets.md |
| Speech-to-text o text-to-speech | lops_stt_tts.md |
| Usar Claude Code LOP | lops_claude_code.md |
| Configurar Tool Manager desde cero | lops_tool_manager.md |
| Exponer un tool_manager a un cliente MCP externo (ChatGPT, etc.) | lops_external_mcp_exposure.md |
| Trabajar con operadores POPX | ../popx/popx_router.md |

---

## Reglas de conducta en proyectos LOPs

- Tras cambios en tools o system_message de un agente: `reinitextensions.pulse()`
- Copiar ops LOPs entre containers: usar `save()` + `loadTox()`, NO `copy()` (va al src)
- No usar Claude Code LOP sin pedir permiso explícito al usuario
- Limpiar tras experimentos: borrar filas de test, destruir operadores copiados
- Doc oficial LOPs: https://docs.dotsimulate.com/
- Mapa visual de operadores: https://docs.dotsimulate.com/map/
