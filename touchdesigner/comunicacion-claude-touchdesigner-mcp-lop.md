> ⚠️ **DEPRECADO** — 29 junio 2026
>
> Este documento está desactualizado. La información útil ha sido redistribuida:
> - Setup y tools del Tool Manager → `td_tool_manager_setup.md`
> - Catálogo de operadores LOPs → `td_lops_catalog.md`
> - Onboarding y conexión → `td_onboarding.md`
> - Errores y pitfalls → `td_pitfalls.md`
> - Snippets reutilizables → `td_snippets.md`
>
> Se mantiene como archivo de referencia histórica por los snippets de §9 que aún no están en otros documentos. No leerlo como fuente de verdad — las rutas, nombres de containers y configuraciones pueden estar desactualizados.

---

# [ARCHIVO HISTÓRICO] Comunicación Claude ↔ TouchDesigner via LOPs

Guía de onboarding para cualquier instancia de Claude que tenga que operar en un proyecto TouchDesigner que use el LOPs pack (dotsimulate).

Audiencia: Claude (cualquier modelo/versión). Asume que tienes acceso al MCP touchdesigner-lop (o equivalente) y a tu propio set de tools internas (view, create_file, bash_tool, etc.).
Origen: experiencia acumulada en el proyecto GIVAH Immersive entre mayo y junio 2026, contrastada con la documentación oficial dotsimulate.
Última revisión: 6 de junio de 2026.

> ⚠️ RUTAS DESACTUALIZADAS: este doc usa `/claude_desktop` como path del Tool Manager. El path correcto ahora es `/claude_desktop_tool_manager`.

---

# 1 · Por qué existe este documento
Si abres una conversación nueva con un usuario que trabaja con TouchDesigner + LOPs y no tienes ningún contexto, lee esto primero. Te explica:

Qué es LOPs y qué problemas resuelve
Cómo conectarte al proyecto y verificar que tienes acceso
Qué operadores LOPs existen y cuándo usar cada uno
Cómo crear un agente de pruebas sin tocar producción
Cómo NO gastar dinero del usuario por error (especialmente Claude Code)
Pitfalls que ya nos hemos comido y deberías evitar

Tu modelo de entrenamiento probablemente no conoce LOPs porque es un pack de terceros que evoluciona rápido. La documentación oficial está en docs.dotsimulate.com y dotdocs.netlify.app, pero NO puedes navegarla via web_search desde dentro de TD (los MCP tools no acceden a la web). Pide al usuario los textos de doc si los necesitas; suele tenerlos a mano.
Existe un mapa visual del ecosistema en https://docs.dotsimulate.com/map/ que muestra qué operadores se relacionan con cuáles. Pide al usuario una captura si necesitas ver el contexto de un operador desconocido.

⚠️ Lectura obligada antes de construir cualquier watcher (datexecuteDAT, parameterexecuteDAT, etc.): §6.10. Las mutaciones que tú haces desde el MCP no disparan los callbacks de manera fiable. Si testeas un watcher con appendRow desde aquí y "no funciona", probablemente el watcher esté bien y el método de test esté roto. Esta lección ha costado horas en proyectos previos.

[... contenido original omitido por brevedad — ver historial de git para el texto completo ...]

## 9 · Apéndice: snippets útiles (AÚN VÁLIDOS)

### 9.1 Listar todos los tools que ve un agente
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
        print(f"  [{i}] {active.eval()} {tool_op.name} → {names}")
```

### 9.2 Reset session de un agente sin perder configuración
```python
ag = op('/project1/agent_XXX')
ag.par.Cancelcall.pulse()
ag.par.Clearsession.pulse()
ag.par.reinitextensions.pulse()
```

### 9.3 Cost guard antes de probar nada
```python
ag = op('/project1/agent_test')
ag.par.Costbudget = 0.05
ag.par.Resetcostmeter.pulse()
```

### 9.4 Buscar logs útiles de un operador
```python
log = op('/project1/<op>/logs')
print(f"{log.numRows} entries")
for r in range(max(1, log.numRows-10), log.numRows):
    print([str(log[r,c].val)[:120] for c in range(min(4, log.numCols))])
```

### 9.5 Auto-conectar un servicio externo al abrir el .toe
```python
s = op('/project1').create(executeDAT, 'startup_<servicio>')
s.par.language = 'python'
s.par.start = True
s.par.active = True
s.text = '''
def onStart():
    try:
        target = op("/project1/<operador_a_conectar>")
        if not target: return
        if hasattr(target.par, "Connected") and target.par.Connected.eval():
            return
        target.par.Connect.pulse()
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

### 9.6 Watcher event-driven sobre DAT de log
```python
w = op('/project1').create(datexecuteDAT, '<nombre>_watcher')
w.par.language = 'python'
w.par.dat = '/ruta/al/log_dat'
w.par.tablechange = True
w.par.sizechange = True
w.par.active = True
w.text = '''
def _check(dat):
    if not dat: return
    key = "prev_rows__" + dat.path
    prev = me.fetch(key, None)
    cur = dat.numRows
    if prev is None:
        me.store(key, cur)
        return
    if cur > prev:
        # procesar filas nuevas [prev, cur)
        pass
    me.store(key, cur)

def onTableChange(dat): _check(dat)
def onSizeChange(dat): _check(dat)
def onRowChange(dat, rows): _check(dat)
def onCellChange(dat, cells, prev): pass
def onColChange(dat, cols): pass
'''
target = op(w.par.dat.eval())
w.store('prev_rows__' + target.path, target.numRows)
```
