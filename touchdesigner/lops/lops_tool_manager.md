# Tool Manager Setup — Claude Desktop ↔ TD

**Qué es:** container TD portátil (`/claude_desktop_tool_manager`) que expone 25 tools via MCP.  
**Puerto:** 18766 (streamable-http, Tool Manager LOP de dotsimulate LOPs)  
**Última revisión:** 29 junio 2026

---

## Conexión rápida (claude_desktop_config.json)

```json
"touchdesigner-lop": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "http://127.0.0.1:18766/mcp"]
}
```

Reiniciar Claude Desktop después de editar el config.

---

## El container

El container `claude_desktop_tool_manager` es un `.tox` portable — se puede copiar entre proyectos.  
Vive en `/claude_desktop_tool_manager` (raíz del proyecto).  
Dentro tiene 12 ops en el Tool sequence + ops de infraestructura.

### Tools activas (25 en total)

| Grupo | Tools | Para qué |
|---|---|---|
| **td_code** | `td_code` | Python con acceso completo a TD globals. Variables NO persisten entre llamadas. |
| **td_mod** | `td_mod` | Módulos curados: `catalog` (buscar tipos de op), `net` (leer red), `search` (descubrir módulos) |
| **tool_dat** | `edit_td_dat_*` (6 tools) | Leer/editar DATs con precisión: set_target, read_content, str_replace, insert, create_dat, check_target |
| **tool_vfs** | `file_tool_*` (7 tools) | Sistema de archivos virtual dentro del container: read, write, list, search, delete, copy, move |
| **tool_op_context** | `network_context` | Ejecutar Python con acceso al proyecto (más permisivo que td_code) |
| **any** | `read`, `ls`, `str_replace`, `insert`, `create`, `undo` | Leer/editar DATs y archivos, navegar la red |
| **tool_monitor** | `get_recent_activity`, `capture_network_screenshot` | Ver actividad reciente del usuario, capturar screenshot de la red |
| **search_web** | `search_web` | Búsqueda web via Serper API (requiere API key configurada) |

### Ops en el container pero fuera del sequence (infraestructura)
- `token_count1` — estimar tokens de texto
- `context_grabber1` — contexto multimodal (TOPs + DATs)
- `tool_debugger1` — inspeccionar schemas de tools
- `tool_registry1` — registro de tools disponibles
- `log_receiver1` — logs centralizados de LOPs
- `storage1` — storage backend (inactivo hasta conectar al graph)
- `graph1` — RAG con grafos (desactivado — requiere Storage backend configurado)

### VFS (sistema de archivos virtual)
El `tool_vfs1` tiene un workspace virtual persistente dentro del container.  
Archivos guardados aquí **viajan con el .tox** — disponibles en cualquier PC.

---

## Arranque en cada sesión

El container arranca automáticamente con TD.  
Si el servidor está caído (Running: Off), desde Claude:
```python
op('/claude_desktop_tool_manager/tool_manager1').par.Restartserver.pulse()
```

Verificar conexión: pedir `get_recent_activity` — si responde, todo OK.

---

## Añadir nuevos ops al Tool Manager

1. Copiar el op LOP desde `/dot_lops/custom_operators/<nombre>` al container.
**No usar `copy()`** — crea el op DENTRO del src. Usar save+loadTox:
```python
import os
tmp = 'C:/Users/<user>/AppData/Local/Temp/lop_copy'
os.makedirs(tmp, exist_ok=True)
src = op('/dot_lops/custom_operators/mi_op')
src.save(f'{tmp}/mi_op1.tox')
container = me.parent()  # desde td_code
new_op = container.loadTox(f'{tmp}/mi_op1.tox')
new_op.name = 'mi_op1'
new_op.nodeX = X; new_op.nodeY = Y
```

2. Añadir al sequence del tool_manager:
```python
tm = op('/claude_desktop_tool_manager/tool_manager1')
seq = tm.par.Tool.sequence
seq.insertBlock(seq.numBlocks - 1)  # insertar al final
# Después de cook:
[p for p in tm.pars(f'Tool{seq.numBlocks-1}op')][0].val = new_op
```

3. Pulsar **Refresh Tools** en el tool_manager1 → pestaña Tools.
4. Pulsar **Restart Server**.
5. Reiniciar Claude Desktop para que detecte las nuevas tools.

---

## Instalar dependencias Python para tools

El container usa el venv de LOPs (`/dot_lops`).  
Abrir Python Manager → Open Console → usar `uv pip install <paquete>`.  
Ejemplo: `uv pip install Pillow` (necesario para `capture_network_screenshot`).

---

## Pitfalls específicos del Tool Manager

- `copy()` de op a otro container crea el op DENTRO del src, no en el target → usar `loadTox()`
- `getattr(tm.par, 'Tool10op')` no funciona tras insertBlock → usar `list(tm.pars('Tool10op'))[0]`
- `seq.insertBlock(N)` con N = numBlocks da error — usar N = numBlocks - 1
- Los ops creados con `td_code` NO persisten (td_code corre en sandbox) → usar `network_context` o `loadTox`
- `tool_parameter` (para exponer pars de ops específicos a agentes) requiere configuración por op — no es genérico
- "Server shutting down" en Textport = normal al cerrar conexión MCP, no es error
