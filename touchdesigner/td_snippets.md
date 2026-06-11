# TouchDesigner - Snippets reutilizables

Codigo reutilizable para tareas comunes en TD y LOPs.

**Ultima revision:** junio 2026.

---

## Listar todos los tools que ve un agente

**Cuando:** al entrar a un proyecto desconocido, o para verificar que tools tiene parseadas un Agent LOP tras cambios en su Tool sequence.

```python
ag = op('/project1/agent_XXX')
n = ag.par.Tool.sequence.numBlocks
print(f"Agent {ag.name}: {n} tool slots, modelo={ag.par.Model.eval()}")
for i in range(n):
    op_par = getattr(ag.par, f'Tool{i}toolop')
    active = getattr(ag.par, f'Tool{i}toolactive')
    tool_op = op_par.eval()
    if tool_op and hasattr(tool_op, 'GetTool'):
        tools = tool_op.GetTool()
        if isinstance(tools, list):
            names = [t.get('tool_definition',{}).get('function',{}).get('name','?') for t in tools]
        elif isinstance(tools, dict):
            names = [tools.get('tool_definition',{}).get('function',{}).get('name','?')]
        else:
            names = ['?']
        print(f"  [{i}] {active.eval()} {tool_op.name} -> {names}")
```

---

## Tester de funcion de modulo en tool_td_mod (sin agente)

**Cuando:** para testear una funcion de un modulo Python en tool_td_mod sin lanzar un agente real (sin coste, sin espera).

```python
import json
tdm = op('/project1/tool_td_mod1')

class MockToolCall:
    def __init__(self, args):
        class _F:
            def __init__(self, a): self.arguments = json.dumps(a)
        self.function = _F(args)

# Listar modulos disponibles
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({"action":"list"})))

# Llamar una funcion concreta
result = tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action":"call",
    "function":"<modulo>.<funcion>",
    "args": {"arg1": "valor1"}
}))
print(json.dumps(result, indent=2, default=str))
```

---

## Reset de sesion de un agente sin perder configuracion

**Cuando:** cuando quieres empezar una conversacion limpia con el mismo agente (mismos tools, mismo system_message) sin borrar ni reconfigurar nada.

```python
ag = op('/project1/agent_XXX')
ag.par.Cancelcall.pulse()
ag.par.Clearsession.pulse()
ag.par.reinitextensions.pulse()
# Resultado: conversacion vacia, mismos tools y system_message
```

---

## Cost guard antes de probar nada

**Cuando:** siempre que vayas a lanzar queries de prueba. Pone un tope de gasto duro para que una llamada no se desmande.

```python
ag = op('/project1/agent_test')
ag.par.Costbudget = 0.05  # 5 centimos maximo por query
ag.par.Resetcostmeter.pulse()
# Lanza query; si supera $0.05 el agente corta automaticamente
```

---

## Buscar logs utiles de un operador

**Cuando:** para diagnosticar que ha pasado en un LOP. Cada LOP suele tener un sub-DAT logs con eventos timestampados.

```python
log = op('/project1/<op>/logs')
print(f"{log.numRows} entries")
for r in range(max(1, log.numRows-10), log.numRows):
    print([str(log[r,c].val)[:120] for c in range(min(4, log.numCols))])
```

---

## Crear un modulo Python para tool_td_mod desde cero

**Cuando:** cuando quieres anadir una nueva funcion al repertorio del agente a traves de tool_td_mod, siguiendo el patron de modulo documentado y tipado.

```python
src_code = '''"""
mi_modulo - descripcion breve.
"""

def hola(nombre: str) -> dict:
    """Saluda a alguien.

    Args:
        nombre: nombre de la persona.

    Returns:
        dict con mensaje.
    """
    if not nombre:
        return {"ok": False, "error": "nombre vacio"}
    return {"ok": True, "mensaje": f"Hola, {nombre}"}
'''

# Compilar para verificar sintaxis antes de crear el DAT
compile(src_code, 'mi_modulo', 'exec')

# Crear o actualizar en el comp modules del tool_td_mod
modules_comp = op('/project1/tool_td_mod1/modules')
existing = modules_comp.op('td_mi_modulo')
if existing:
    existing.text = src_code
else:
    dat = modules_comp.create(textDAT, 'td_mi_modulo')
    dat.text = src_code

# Verificar que aparece en el schema del tool
print(op('/project1/tool_td_mod1').GetTool()['tool_definition']['function']['parameters']['properties']['args']['description'])
```

---

## Auto-conectar un servicio externo al abrir el .toe

**Cuando:** para LOPs con bridges o conexiones externas (claude_codeLOP, MCP servers, sockets) que no se conectan solos al cargar el proyecto. Un executeDAT con start=True lanza el handshake automaticamente. Es idempotente: si ya esta conectado, el pulse no hace nada.

```python
s = op('/project1').create(executeDAT, 'startup_<servicio>')
s.par.language = 'python'
s.par.start = True   # CRITICO: dispara onStart al cargar el .toe
s.par.active = True

s.text = '''
def onStart():
    try:
        target = op("/project1/<operador_a_conectar>")
        if not target:
            return
        if hasattr(target.par, "Connected") and target.par.Connected.eval():
            print("[startup] ya estaba conectado")
            return
        target.par.Connect.pulse()
        print("[startup] conectado")
    except Exception as e:
        print(f"[startup] error: {e}")

def onCreate(): pass
def onExit(): pass
def onFrameStart(frame): pass
def onFrameEnd(frame): pass
def onPlayStateChange(state): pass
def onDeviceChange(): pass
def onProjectPreSave(): pass
def onProjectPostSave(): pass
'''
```

Generalizable a cualquier handshake de arranque: cargar caches, inicializar workers, restablecer suscripciones.

---

## Watcher event-driven sobre un DAT de log

**Cuando:** para vigilar una tabla que crece monotonicamente (como un log) y reaccionar SOLO a filas nuevas que cumplan un criterio. Usa me.storage para persistir el estado entre disparos.

> ATENCION al testear: los appendRow desde el MCP no disparan los callbacks de este watcher
> (ver td_pitfalls.md seccion callbacks datexecuteDAT). Para validar, lanza una operacion
> real del operador que normalmente escribe en el log, o invoca el callback directamente.

```python
w = op('/project1').create(datexecuteDAT, '<nombre>_watcher')
w.par.language = 'python'
w.par.dat = '/ruta/al/log_dat'
w.par.tablechange = True
w.par.sizechange = True
w.par.rowchange = True
w.par.active = True

w.text = '''
def _process_new_rows(dat, n_old, n_new):
    target_col = -1
    for c in range(dat.numCols):
        if str(dat[0, c].val) == "<columna_filtro>":
            target_col = c
            break
    if target_col < 0:
        return
    for r in range(n_old, n_new):
        try:
            valor = str(dat[r, target_col].val)
        except Exception:
            continue
        if valor == "<valor_que_buscamos>":
            try:
                mod = op("/project1/tu_modulo").module
                mod.on_event(r, dat)
            except Exception as e:
                print(f"[watcher] error: {e}")

def _check(dat):
    if not dat:
        return
    key = "prev_rows__" + dat.path
    prev = me.fetch(key, None)
    cur = dat.numRows
    if prev is None:
        me.store(key, cur)
        return
    if cur > prev:
        _process_new_rows(dat, prev, cur)
    me.store(key, cur)

def onTableChange(dat): _check(dat)
def onRowChange(dat, rows): _check(dat)
def onSizeChange(dat): _check(dat)
def onCellChange(dat, cells, prev): pass
def onColChange(dat, cols): pass
'''

# Inicializar contador para no procesar el historico existente
target = op(w.par.dat.eval())
w.store('prev_rows__' + target.path, target.numRows)
```

Para repuntar el watcher si el DAT objetivo cambia de ruta:

```python
def onValueChange(par, prev):
    new_path = "/nueva/ruta/calculada"
    watcher = op("/project1/<nombre>_watcher")
    watcher.par.dat = new_path
    watcher.store("prev_rows__" + new_path, op(new_path).numRows)
```

---

## Scroll e interaccion de raton en webrenderTOP usado como panel

**Cuando:** tienes un `webrenderTOP` como background de un `containerCOMP` y necesitas que el scroll y los clicks del usuario lleguen al navegador CEF. No se reenvian automaticamente — hay que crear un `panelexecDAT` dentro del container.

**Configuracion del panelexecDAT:**
- `panelvalue` = `lselect mselect rselect wheel insideu insidev`
- `valuechange` = True

```python
# panelexecDAT — unico patron fiable
def onValueChange(panelValue):
    p = panelValue.owner.panel
    op('web1').interactMouse(
        p.insideu, p.insidev,
        left=bool(p.lselect), middle=bool(p.mselect),
        right=bool(p.rselect), wheel=p.wheel
    )
```

Lee los valores directamente de `panelValue.owner.panel` en cada disparo. No calcules deltas — pasa el estado instantaneo.

**Actualizaciones dinamicas de la UI desde TD (sin interaccion del usuario):**

```python
# Unidireccional TD->web, ligero
op('web1').executeJavaScript("miFuncion(args)")
```

No usar `sessionStorage` restore con `setTimeout` para esto — lucha con el scroll del usuario.

> Anti-patrones documentados en td_pitfalls.md (seccion webrenderTOP scroll).
