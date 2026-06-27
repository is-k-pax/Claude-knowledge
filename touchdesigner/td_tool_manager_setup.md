# TouchDesigner — Tool Manager Setup (Claude Desktop)

Cómo montar la infraestructura Tool Manager en cualquier proyecto TD para
que Claude tenga acceso ampliado via `td_mod` y `td_code`, además del MCP LOP base.

**Origen:** sesión de experimentación junio 2026.  
**Última revisión:** 27 de junio de 2026.

---

## Por qué montar esto

El MCP LOP (puerto 18555) da acceso a TD pero con limitaciones:
- Cada `execute_python` es una llamada aislada — sin persistencia de variables entre llamadas
- Para explorar la red hay que ir nodo a nodo

Con Tool Manager + Tool TD Code + Tool TD Mod se añaden dos herramientas nuevas:

| Tool | Qué aporta |
|---|---|
| `td_code` | Python con sesión persistente entre llamadas. Las variables definidas en una llamada existen en la siguiente. |
| `td_mod` | Catálogo de módulos curados: `td_net` (leer/escribir redes como texto), `td_catalog` (buscar tipos de ops), `td_search` (descubrir módulos) |

`td_net` es especialmente potente: `summary('/comp')` devuelve toda la red como texto estructurado, `apply('/comp', texto)` aplica cambios. Permite leer y modificar redes enteras sin ir nodo a nodo.

---

## Setup: cómo preparar un proyecto nuevo

### Paso 1 — Montar el COMP `/claude_desktop`

En tu proyecto TD, crea un Container COMP llamado `claude_desktop` en la raíz `/`.
Dentro coloca estos tres operadores LOPs (via OP Create Dialog):
- `tool_td_mod` → quedará como `tool_td_mod1`
- `tool_td_code` → quedará como `tool_td_code1`
- `tool_manager` → quedará como `tool_manager1`

No hace falta conectarlos entre sí visualmente — el Tool Manager los referencia por path.

### Paso 2 — Decirle a Claude que entre y configure

Con el MCP LOP (18555) activo, escribe:
> "Entra en el proyecto y configura `/claude_desktop` para que pueda usar td_mod y td_code"

Claude ejecutará el script de configuración automáticamente (ver sección siguiente).

### Paso 3 — Añadir el servidor al claude_desktop_config.json

El Tool Manager corre en el puerto **18766**. Añadir a `mcpServers`:

```json
"td_tool_manager": {
  "command": "npx",
  "args": ["-y", "mcp-remote", "http://127.0.0.1:18766/mcp"]
}
```

Reiniciar Claude Desktop. A partir de ahí Claude tiene disponibles `td_mod` y `td_code`.

---

## Script de configuración (Claude lo ejecuta via MCP LOP)

Este script asume que los tres operadores ya existen en `/claude_desktop`.
Claude lo ejecuta via `execute_python` cuando se le pide configurar el setup.

```python
tm = op('/claude_desktop/tool_manager1')
ext = tm.ext.ToolMCPBridgeEXT

# 1. Conectar ChatTD (requerido para el servidor async)
chattd = op('/dot_lops/ChatTD')
if chattd:
    tm.par.Chattd = chattd.path

# 2. Asignar tool_td_mod1 al slot 0
tm.par['Tool0op'] = '/claude_desktop/tool_td_mod1'
tm.par['Tool0active'] = 'enabled'

# 3. Expandir secuencia y asignar tool_td_code1 al slot 1
seq = tm.par['Tool'].sequence
if seq.numBlocks < 2:
    seq.insertBlock(0)  # inserta al principio, desplaza el existente
tm.par['Tool1op'] = '/claude_desktop/tool_td_code1'
tm.par['Tool1active'] = 'enabled'

# 4. Refresh de tools y arrancar servidor
ext.Refreshtools()
tm.par.Startserver.pulse()

# Verificar
print(f"Tool0op: {tm.par['Tool0op'].val}")
print(f"Tool1op: {tm.par['Tool1op'].val}")
print(f"Servidor URL: {tm.par.Serverurl.val}")
```

**Nota sobre el insertBlock:** al insertar en índice 0 la secuencia se desplaza:
- El nuevo bloque vacío queda en Tool0
- El bloque original (tool_td_mod) queda en Tool1
Por eso tras el insert hay que reasignar Tool0op a tool_td_mod y Tool1op a tool_td_code.
O insertar en índice 1 directamente si ya hay un bloque — pero insertBlock(1) da error si
numBlocks es 1. La forma segura es insertar en 0 y reescribir ambos slots.

---

## Verificar que todo funciona

Desde Claude Desktop (chat nuevo tras reiniciar), buscar las herramientas:
- `td_mod` con `action=call, function=search.index` → debe devolver los 3 módulos
- `td_code` con `code="print(project.cookRate)"` → debe devolver el FPS

---

## Módulos disponibles en td_mod

| Módulo | Para qué |
|---|---|
| `net` (`td_net`) | Leer redes: `net.summary('/comp')`. Escribir: `net.apply('/comp', texto)`. Crear ops: `net.mk(parent, tipo, nombre)`. Ver diff: `net.diff(antes, después)`. |
| `catalog` (`td_catalog`) | Buscar tipos de operadores: `catalog.search('noise')`, `catalog.types('TOP')` |
| `search` (`td_search`) | Descubrir módulos disponibles: `search.index()`, `search.find('query')`, `search.read('td_net')` |

---

## Notas importantes

- El servidor Tool Manager (18766) es **adicional** al MCP LOP (18555). Ambos pueden estar activos a la vez.
- Si TD se reinicia, hay que volver a pulsar Start Server en tool_manager1 (o pedirle a Claude que lo haga via MCP LOP).
- El ChatTD en `/dot_lops/ChatTD` es requerido para el servidor async. Si no existe, el servidor no arranca.
- `td_code` tiene variables persistentes **dentro de una sesión** de Claude Desktop. Si cierras y abres Claude, la sesión se resetea.
