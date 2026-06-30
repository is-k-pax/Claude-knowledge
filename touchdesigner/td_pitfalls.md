# TouchDesigner — Pitfalls acumulados

Errores y trampas descubiertas trabajando con TD y LOPs. Antes de asumir que tu código está mal, revisa esta lista.

**Última revisión:** 30 de junio de 2026.

---

## ⚠️ Posición de nodos al crearlos con Python

Al crear operadores con `comp.create(tipo, 'nombre')`, TD los coloca en `x=0, y=0` por defecto. Si se crean varios seguidos sin asignar posición, **quedan todos apilados en el mismo punto** — visualmente solo se ve uno encima de los demás.

**Siempre** asignar `nodeX` y `nodeY` inmediatamente después de crear cada operador. Primero leer dónde están los operadores existentes para elegir una zona libre:

```python
for c in comp.children:
    print(f"{c.name}: x={c.nodeX}, y={c.nodeY}")

n1 = comp.create(speedCHOP, 'mi_speed')
n1.nodeX = -575; n1.nodeY = 650
```

**Convención de espaciado:** ~200 unidades en X, ~125 en Y. Misma cadena → mismo Y.

---

## ⚠️ net.apply() trunca expresiones Python con comas

`net.apply()` parsea el texto de la red y trunca expresiones con **comas dentro de paréntesis**.

**Síntoma:** `SyntaxError: '(' was never closed`. El valor queda a 0.

**Fix:** usar `td_code` directamente para expresiones complejas:
```python
op('/mi/comp').par['vec2valuex'].expr = "tdu.remap(math.sin(op('x')['chan1'] * 6.28), -1, 1, 3.0, 5.5)"
```

**Regla:** `net.apply()` OK para valores numéricos y expresiones simples. Comas internas → `td_code`.

---

## Threading y cook

- `time.sleep()` >1s dentro de `execute_python` **BLOQUEA el cook thread** → timeout MCP.
- TD no es multithread. Lo costoso: asincrónico o aceptar frames perdidos.

## Agent LOP

- `Active` flickea a False entre tool_calls batcheados
- `Clearsession.pulse()` en flight → orphaned callback 20-30s. Fix: `reinitextensions.pulse()`
- Tras cambios en `seq.Tool` o `system_message`: SIEMPRE `reinitextensions.pulse()`
- `Maxresultchars` default 16K — trunca silenciosamente. Poner 250000
- Para añadir slot: `ag.par.Tool.sequence.numBlocks = N` (no `ag.par.Tool.val = N`)

## Tool DAT v2.4.0

- Cada Tool DAT necesita `Toolname` DISTINTO. Default `edit_td_dat` → `DUPLICATE TOOL — ALL TOOLS DISABLED`
- `view_range` solo aplica a Text DAT, no Table DAT

## Tool Manager

- Añadir slots: `Refreshtools.pulse()` + `Restartserver.pulse()`
- `server_state` JSON es la verdad, no el parámetro `Running`
- "Server shutting down" en Textport = normal al cerrar conexión MCP, no es error

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

## ⚠️ getattr(tm.par, 'Tool10op') no funciona tras insertBlock

Tras `seq.insertBlock()`, los nuevos pars no son accesibles via `getattr`.
Usar: `list(tm.pars('Tool10op'))[0]`

Los pars OP pueden perderse tras `cook(force=True)` — reasignar siempre después del cook.

## ⚠️ td_code corre en sandbox — cambios no persisten al container real

Los ops creados con `td_code` NO son visibles desde `network_context` ni desde TD.

**Para crear ops que persistan:** usar `network_context` o el método `loadTox()` desde `td_code`.

## ⚠️ seq.insertBlock(N) con N = numBlocks da error

`insertBlock` acepta índices 0 a numBlocks-1.
Para insertar al final: `seq.insertBlock(seq.numBlocks - 1)`

## Operadores TD genéricos

- `baseCOMP` no permite interacción de panel → usar `containerCOMP`
- DAT Execute con re-entrancia: `me.storage["processing"] = True`
- `webserverDAT.par.transparent` (minúscula)
- `parameterexecuteDAT.par.pars` (no `parameters`)
- textDATs como callbacks: `language=python` explícito (default text, silent skip)

## webserverDAT headers

```python
response["Access-Control-Allow-Origin"] = "*"  # ✓
# response["headers"] = {"...": "..."}          # ✗ NO como sub-dict
```

## ⚠️ Callbacks de datexecuteDAT NO disparan desde el MCP

`op(...).appendRow([...])` via MCP modifica la tabla pero los `datexecuteDAT` no reciben callbacks.

**Testear correctamente:** llamar callback directamente o disparar desde dentro de TD.

## me.storage para estado persistente en DAT executes

```python
def onTableChange(dat):
    key = "prev_rows__" + dat.path
    prev = me.fetch(key, None)
    cur = dat.numRows
    if prev is not None and cur > prev:
        pass  # procesar filas nuevas
    me.store(key, cur)
```

## ⚠️ me.storage + absTime.frame: timestamps que sobreviven al reinicio de TD

`me.storage` persiste con el `.toe`. `absTime.frame` se reinicia cada vez que arranca TD.

Si guardas `t_inicio = absTime.frame` y el `.toe` se reabre, el nuevo frame puede ser menor → progreso negativo → valores absurdos en curvas de easing.

**Fix:**
```python
def tick():
    ahora = absTime.frame
    info = me.fetch('mi_animacion', None)
    if info is None: return
    if ahora < info['t_inicio']:
        t_raw = 1.0
    else:
        t_raw = (ahora - info['t_inicio']) / info['duracion']
    t_raw = max(0.0, min(1.0, t_raw))  # clamp defensivo, SIEMPRE
```

## ⚠️ webrenderTOP scroll: anti-patrones que NO funcionan

El scroll y clicks NO se reenvían automáticamente del containerCOMP al webrenderTOP.

**NO funciona:** `panelCHOP` + `chopexecuteDAT` con canal `wheel` (es pulso 0/1, no float), listeners JS `addEventListener('wheel')`, `sessionStorage` restore con `setTimeout`.

**SÍ funciona:** `panelexecDAT` con `valuechange=True` llamando `web.interactMouse()` directamente.
