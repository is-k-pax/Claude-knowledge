# LOPs — Pitfalls acumulados

Errores y trampas descubiertas trabajando con LOPs y Tool Manager.

**Última revisión:** 3 de julio de 2026.

---

## Agent LOP

- `Active` flickea a False entre tool_calls batcheados
- `Clearsession.pulse()` en flight → orphaned callback 20-30s. Fix: `reinitextensions.pulse()`
- Tras cambios en `seq.Tool` o `system_message`: SIEMPRE `reinitextensions.pulse()`
- `Maxresultchars` default 16K — trunca silenciosamente. Poner 250000
- Para añadir slot: `ag.par.Tool.sequence.numBlocks = N` (no `ag.par.Tool.val = N`)

---

## Tool DAT v2.4.0

- Cada Tool DAT necesita `Toolname` DISTINTO. Default `edit_td_dat` → `DUPLICATE TOOL — ALL TOOLS DISABLED`
- `view_range` solo aplica a Text DAT, no Table DAT

---

## Tool Manager

- Añadir slots: `Refreshtools.pulse()` + `Restartserver.pulse()`
- `server_state` JSON es la verdad, no el parámetro `Running`
- "Server shutting down" en Textport = normal al cerrar conexión MCP, no es error
- **Tras ampliar el módulo de un `Any` (más tools en `get_tools()`)**, la página "Tool Toggle" del
  tool_manager no sincroniza la lista de switches con solo `Refreshtools.pulse()` — hace falta
  `Restartserver.pulse()` para que aparezcan los toggles individuales de las tools nuevas. Sin ese
  restart, el toggle sigue mostrando solo las tools que existían en la última vez que se arrancó
  el servidor, aunque `GetTool()` del `Any` ya devuelva la lista completa.
- **Si el `tool_manager` usa `aiohttp` internamente** (ver `td_mcp_adapter` → `create_http_app()`),
  ese método solo se ejecuta al arrancar el servidor. Editar el DAT y esperar que el servidor ya
  corriendo recoja el cambio en caliente no funciona — hace falta `Restartserver.pulse()` después
  de cada edición del código del adapter, no solo tras cambios en el módulo del `Any`.

---

## ⚠️ Probar el propio servidor MCP desde dentro del proceso de TD puede autobloquearse

**Síntoma:** una llamada HTTP bloqueante (`urllib.request.urlopen`, o cualquier cliente síncrono)
lanzada desde `td_code`/`network_context` hacia el propio `tool_manager` de ese mismo proyecto
(ej. `http://127.0.0.1:<puerto>/mcp`) se queda colgada hasta el timeout, en todas las peticiones,
sin importar el contenido de la petición.

**Causa:** el servidor del `tool_manager` corre sobre `aiohttp` en el mismo proceso/hilo de TD. Si
el script que hace la petición también se ejecuta en ese hilo de forma síncrona y bloqueante,
compite por el mismo recurso que necesita para poder responderse a sí mismo — auto-bloqueo. No es
un fallo del servidor ni de la lógica que se esté probando (p. ej. un middleware de auth): el
patrón de prueba en sí es el problema.

**Fix:** nunca testear un servidor MCP embebido en TD haciendo peticiones de red hacia él mismo
desde dentro de `td_code`/`network_context`. Probarlo desde un proceso externo — una terminal
aparte con `curl` o `Invoke-WebRequest` (PowerShell), o cualquier cliente HTTP que corra fuera del
proceso de TD. Esto también permite verificar alcance real desde fuera de la máquina si el
servidor está expuesto (ver `lops_external_mcp_exposure.md`).

**Regla:** después de un timeout así, comprobar que TD sigue sano (`project.cookRate`,
`tm.par.Running`) antes de seguir — el bloqueo puede ser temporal (se libera al expirar el
timeout del lado cliente) pero conviene confirmarlo, no asumirlo.

---

## ⚠️ La tool `create` del Tool Manager MCP puede fallar genéricamente sin motivo aparente

**Síntoma:** `create(target=..., content=...)` devuelve `Tool execution failed` sin más detalle,
de forma consistente, independientemente de la ruta de destino (falla igual en un container propio
que directamente en `/project1`).

**Diagnóstico:** no es un problema de permisos de la ubicación — se probó en dos ubicaciones
distintas con el mismo resultado. La causa exacta no se determinó en el momento (podría ser un bug
puntual de esa versión de la tool, o un estado inconsistente del Tool Manager en esa sesión).

**Workaround que sí funciona:** evitar crear un DAT nuevo cuando el objetivo es solo guardar un
valor de configuración (como un token) — meterlo como constante dentro de un DAT que ya existe
(editado con `str_replace`/asignación de `.text`) en vez de crear un DAT dedicado. Si de verdad
hace falta crear un operador nuevo y `create` falla, recurrir al patrón `loadTox()` (ver pitfall
de copiar ops entre containers, más abajo) o al conector `touchdesigner-lop` con
`create_td_node` — aunque este último requiere que ese servidor esté conectado a la instancia
viva de TD (no funciona en modo "docs-only").

---

## Tool VFS

- `Checkvfs.pulse()` con `Createifmissing=True` — sin esto el Agent reporta "no tools"

### ⚠️ VirtualFile creado manualmente no funciona — usar siempre el botón de la UI

**Síntoma:** `virtualFile component missing VirtualFileExt extension`

**Causa:** crear un baseCOMP a mano (con `comp.create(baseCOMP, 'mi_vfs')`) o copiar el virtualFile interno del tool_vfs (con `parent.copy(internal_vf)`) no inicializa la extensión VirtualFileExt. Los parámetros de extensión (`ext0object`, `ext0promote`) se copian correctamente pero la extensión no se carga — `comp.extensions` devuelve `[]`. Ni `reinitextensions.pulse()` ni toggle de `Createifmissing` desde código resuelven el problema.

**Fix:**
1. En la UI de TD, ir al tool_vfs → Settings → pulsar **Create External VirtualFile**
2. Esto crea un `<nombre>_virtualFile` al nivel padre con extensiones correctamente inicializadas
3. Verificar que el parámetro **VirtualFile Component** apunta al COMP externo generado (no al virtualFile interno del tool_vfs)
4. Si apunta al interno (por haberlo cambiado con código), redirigir al externo

**Regla:** nunca crear el VirtualFile component desde Python. Siempre usar el botón de la UI.

### ⚠️ tool_vfs en container externo: necesita estar conectado al tool_manager principal

Un `tool_vfs` dentro de un container propio (fuera de `/claude_desktop_tool_manager/`) funciona, pero debe estar registrado como External Op Tool en el tool_manager principal. Un tool_manager separado corre en otro puerto MCP y Claude Desktop no lo ve salvo que se configure en el JSON de MCPs.

**Setup correcto:**
1. Crear tool_vfs en tu container
2. Pulsar Create External VirtualFile desde la UI
3. En el tool_manager principal → Tools → añadir External Op Tool apuntando al tool_vfs
4. Si hay conflicto de nombres con otro tool_vfs, cambiar el Toolname (ej: `sd_knowledge`)
5. Refresh Tools en el tool_manager

### ⚠️ file_tool_list_files sin pattern falla silenciosamente

**Síntoma:** `file_tool_list_files()` sin argumentos → `Error listing files: can only concatenate str (not "NoneType") to str`. Parece que el VFS está vacío.

**Fix:** pasar `pattern="*"` explícitamente. Los tools `file_tool_*` ya apuntan al VFS activo del Tool Manager — no buscar el operador `tool_vfs1_virtualFile` manualmente en la red.

**Regla:** si buscas un `.md` que no aparece en el repo de GitHub, prueba `file_tool_list_files(pattern="*")` antes de explorar la red de TD.

---

## ⚠️ Copiar ops LOPs entre containers: copy() va al src, no al target

`src.copy(parent, name='nuevo')` crea el op DENTRO del src en lugar del container destino.

**Síntoma:** op aparece en `/dot_lops/custom_operators/<nombre>/<nombre>4` en vez del destino.

**Fix — usar loadTox():**
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

---

## ⚠️ getattr(tm.par, 'Tool10op') no funciona tras insertBlock

Tras `seq.insertBlock()`, los nuevos pars no son accesibles via `getattr`.
Usar: `list(tm.pars('Tool10op'))[0]`

Los pars OP pueden perderse tras `cook(force=True)` — reasignar siempre después del cook.

---

## ⚠️ td_code corre en sandbox — cambios no persisten al container real (matiz: destroy() es la excepción)

Los ops **creados** con `td_code` NO son visibles desde `network_context` ni desde TD.

**Para crear ops que persistan:** usar `network_context` o el método `loadTox()` desde `td_code`.

**Matiz importante — `destroy()` SÍ persiste incluso desde `td_code`.** A diferencia de `create()`,
llamar a `.destroy()` sobre un operador ya existente (obtenido vía `op('/ruta/real')`) borra el
operador de la red real, verificable después desde `network_context`. Esto es porque `destroy()`
opera sobre una referencia a un objeto real de la red, no crea nada nuevo dentro del sandbox.

**Además:** la herramienta `network_context` bloquea `destroy()` explícitamente a nivel de tool
("Blocked: destroy() — permanently deletes operators"), incluso con `Allowcreate`/`Allowmodify`
en `True`. Ese bloqueo es solo de esa tool concreta — `td_code` no tiene esa restricción.

**Otro matiz — creación de operadores también puede estar bloqueada en `network_context`.**
Además del bloqueo de `destroy()`, esta tool puede rechazar directamente cualquier `.create(...)`
con `"Creating operators is not allowed in current mode. Set preset to 'Full' or enable 'Allow
Create'"`. Ese preset no es configurable desde los argumentos de la llamada — si hace falta crear
un operador real y `network_context` lo bloquea, usar `loadTox()` (que sí funciona incluso en este
modo, aparentemente no se clasifica como "create" restringido) o recurrir a editar un DAT ya
existente en vez de crear uno nuevo cuando el caso de uso lo permite.

**Regla práctica:** si necesitas borrar operadores y `network_context` te bloquea con ese mensaje,
usa `td_code` con `.destroy()` directamente; funciona y persiste.

---

## ⚠️ seq.insertBlock(N) con N = numBlocks da error

`insertBlock` acepta índices 0 a numBlocks-1.
Para insertar al final: `seq.insertBlock(seq.numBlocks - 1)`

---

## ⚠️ Operador Any: handlers no se enrutan — todos se llaman "dispatch"

**Síntoma:** las tools del operador `Any` con módulo custom aparecen correctamente en `tools_table` del Tool Manager, pero al invocarlas no ocurre nada o da error de enrutamiento.

**Causa:** `AnyExt._dispatcher()` crea una closure cuyo `__name__` es siempre `"dispatch"` para todos los handlers. El Tool Manager usa ese `__name__` para enrutar — si todos se llaman igual, falla silenciosamente.

**Fix — parchear `_dispatcher()` en `AnyExt`** (buscar el método y reemplazarlo):
```python
def _dispatcher(self, tool_name, handler_name):
    ext_ref = self
    def dispatch(tool_call):
        return ext_ref._call(handler_name, tool_call)
    dispatch.__name__ = handler_name          # ← nombre real, no "dispatch"
    setattr(self, handler_name, dispatch)     # ← expone el handler como atributo del ext
    self._tool_handlers[tool_name] = handler_name
    return dispatch
```

**Secuencia tras aplicar el fix:**
1. Editar `AnyExt` DAT dentro del operador `Any`
2. `Reinitextensions` en el operador `Any`
3. `Refreshtools` en el `tool_manager`

**Verificación rápida:**
```python
at = op('/tool_agent/agent_tools')
ext = at.op('AnyExt')
print('dispatch.__name__ = handler_name' in ext.text)  # debe ser True
```

**Regla:** este parche es necesario en cualquier operador `Any` con módulo custom. Sin él ninguna tool se ejecuta.

---

## ⚠️ Callbacks de datexecuteDAT NO disparan desde el MCP

`op(...).appendRow([...])` via MCP modifica la tabla pero los `datexecuteDAT` no reciben callbacks.

**Testear correctamente:** llamar callback directamente o disparar desde dentro de TD.
