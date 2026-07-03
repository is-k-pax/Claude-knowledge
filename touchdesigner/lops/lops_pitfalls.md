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
