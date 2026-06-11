# Router — lee esto primero

**Repo:** is-k-pax/Claude-knowledge (público, editable via GitHub MCP)

---

## Qué documento leer según la situación

| Situación | Lee primero | Luego si necesitas más |
|---|---|---|
| Entro a un proyecto TouchDesigner | `touchdesigner/td_onboarding.md` | `touchdesigner/td_lops_catalog.md` |
| Necesito código TD reutilizable | `touchdesigner/td_snippets.md` | — |
| Algo falla en TD o LOPs | `touchdesigner/td_pitfalls.md` | — |
| Me piden crear un tool nuevo para un agente | `touchdesigner/td_tool_creation.md` | — |
| Me planteo usar Claude Code LOP | `touchdesigner/td_claude_code.md` | — |
| Me piden un shader GLSL en TD | `touchdesigner/glsl/glsl_fundamentals.md` | `touchdesigner/glsl/glsl_patterns.md` |
| Problema de MCP (timeout, conexión, SHA) | `general/mcp_troubleshooting.md` | — |
| Entro a Resolume | `resolume/resolume_onboarding.md` | — |
| Entro a Ableton | `ableton/ableton_onboarding.md` | — |
| Entro a ComfyUI | `comfyui/comfyui_onboarding.md` | — |

---

## Cuando descubras algo nuevo trabajando

1. Decide la categoría: ¿es un pitfall? ¿un snippet? ¿un workflow? ¿conocimiento nuevo?
2. Lee el documento correspondiente del repo via GitHub MCP — **nunca edites desde memoria**
3. Añade la sección nueva siguiendo el formato que ya tiene el documento
4. Haz commit con mensaje: `[carpeta] acción breve`

---

## Reglas del repo

1. **Leer antes de editar.** Siempre hacer `get_file_contents` del archivo antes de modificarlo.
2. **Archivos < 10KB.** Si uno crece más, propón al usuario dividirlo.
3. **Commits:** formato `[carpeta] acción breve` (ej: `[touchdesigner] añade pitfall sobre timeout de MCP`)
4. **Cero datos personales.** Nada de nombres de usuario, rutas locales (`C:\Users\...`), tokens ni contraseñas. El repo es público.
5. **Un archivo por commit.** `push_files` con múltiples archivos falla con payloads grandes.
