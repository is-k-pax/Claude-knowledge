# Router — lee esto primero

**Repo:** is-k-pax/Claude-knowledge (público, editable via GitHub MCP)

---

## Qué documento leer según la situación

### TouchDesigner
| Situación | Lee primero | Luego si necesitas más |
|---|---|---|
| Entro a un proyecto TD | touchdesigner/td_onboarding.md | touchdesigner/td_lops_catalog.md |
| Necesito código TD reutilizable | touchdesigner/td_snippets.md | — |
| Algo falla en TD o LOPs | touchdesigner/td_pitfalls.md | — |
| Crear un tool nuevo para un agente | touchdesigner/td_tool_creation.md | — |
| Configurar Tool Manager para Claude Desktop | touchdesigner/td_tool_manager_setup.md | — |
| Qué operadores LOPs existen y para qué sirven | touchdesigner/td_lops_catalog.md | — |
| Usar Claude Code LOP | touchdesigner/td_claude_code.md | — |
| Me piden un shader GLSL | touchdesigner/glsl/glsl_writing_patterns.md | touchdesigner/glsl/glsl_utils_reference.md |
| Shader para el container shader_changer_01 | touchdesigner/glsl/glsl_container_architecture.md | touchdesigner/glsl/glsl_writing_patterns.md |
| Algo falla en un shader GLSL | touchdesigner/glsl/glsl_pitfalls.md | — |
| Necesito código GLSL reutilizable | touchdesigner/glsl/glsl_snippets.md | — |

### ComfyUI
| Situación | Lee primero | Luego si necesitas más |
|---|---|---|
| Entro a ComfyUI o primera vez | comfyui/comfyui_onboarding.md | — |
| Quiero generar un vídeo desde imagen | comfyui/comfyui_workflows.md | comfyui/comfyui_onboarding.md |
| Quiero editar/mezclar dos imágenes | comfyui/comfyui_workflows.md | comfyui/comfyui_onboarding.md |
| Quiero usar un workflow guardado | comfyui/comfyui_workflows.md | — |
| Arrancar ComfyUI desde PC de casa | comfyui/comfyui_remote_setup.md | — |
| Configurar acceso remoto Tailscale+SSH | comfyui/comfyui_remote_setup.md | — |
| Algo falla en ComfyUI | comfyui/comfyui_onboarding.md | — |

### Figma
| Situación | Lee primero |
|---|---|
| Trabajar con Figma via MCP | figma/figma_onboarding.md |
| Exportar assets de Figma a disco | figma/figma_export.md |
| Algo falla con Figma | figma/figma_pitfalls.md |

### Resolume
| Situación | Lee primero |
|---|---|
| Entro a Resolume | resolume/resolume_onboarding.md |

### Ableton
| Situación | Lee primero |
|---|---|
| Entro a Ableton | ableton/ableton_onboarding.md |

### General
| Situación | Lee primero |
|---|---|
| Problema de MCP (timeout, conexión) | general/mcp_troubleshooting.md |

---

## Dónde guardar lo que aprendo

Cuando descubras algo nuevo durante una sesión, clasifícalo así:

### ¿Qué tipo de conocimiento es?

**Un error y su solución** → `<programa>/pitfalls.md`
Formato: título descriptivo, síntoma, causa, fix.

**Código reutilizable** → `<programa>/snippets.md`
Formato: título de lo que hace, cuándo usarlo, código mínimo.

**Cómo conectar o configurar una herramienta** → `<programa>/onboarding.md`
Añadir a la sección relevante del onboarding existente.

**Un workflow o pipeline completo** → `<programa>/workflows.md`
Crear si no existe. Formato: qué resuelve, pasos, código si aplica.

**Conocimiento específico de un tema** → archivo dedicado
Ejemplo: todo sobre STT → `touchdesigner/td_stt.md`
Ejemplo: exportar assets de Figma → `figma/figma_export.md`
Solo crear archivo nuevo si el tema es lo bastante grande (>1KB) y distinto.

### ¿Es universal o del proyecto actual?

**Universal** (serviría en otro proyecto) → va al repo.
**Específico del proyecto** (configuración particular, operadores concretos de este proyecto) → NO va al repo, se queda en el MASTER.md del proyecto.

### Procedimiento

1. Identificar categoría y programa
2. Leer el archivo destino con github:get_file_contents
3. Añadir al final de la sección relevante
4. Verificar que no hay datos personales ni rutas locales
5. Commit: `[carpeta] acción breve`

### Si el programa no tiene carpeta todavía

Crear la carpeta con un `onboarding.md` mínimo:
