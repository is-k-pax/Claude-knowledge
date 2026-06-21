# TouchDesigner — Pitfalls acumulados

Errores y trampas descubiertas trabajando con TD y LOPs. Antes de asumir que tu código está mal, revisa esta lista.

**Última revisión:** junio 2026.

---

## Threading y cook

- `time.sleep()` >1s dentro de `execute_python` **BLOQUEA el cook thread**. Bridges desconectan, tool_use queda stuck, MCP da timeout a 4 minutos. Solución: queries cortas en múltiples invocaciones separadas del MCP.
- TD no es multithread en cooking. Lo costoso: asincrónico o aceptar frames perdidos.

## Agent LOP

- `Active` flickea a False entre tool_calls batcheados — usar combinación con `Agentstatus` y `turn_table.numRows`
- `conversation_dat` puede parecer vacío visualmente. La verdad: `_api_messages` interno o `turn_table`
- `Clearsession.pulse()` en flight → orphaned callback 20-30s. Fix: `reinitextensions.pulse()`
- Tras cambios en `seq.Tool` o `system_message`: SIEMPRE `reinitextensions.pulse()`
- `Maxresultchars` default 16K, clampMax 100K — trunca silenciosamente. Poner 250000
- Para añadir slot: `ag.par.Tool.sequence.numBlocks = N` (no `ag.par.Tool.val = N`)
- El agente lee de `<agent>/system_prompt`, no del DAT en `Systemmessagedat`. Propagar a ambos.

## Tool DAT v2.4.0

- Cada Tool DAT necesita `Toolname` DISTINTO. Default `edit_td_dat` → `DUPLICATE TOOL — ALL TOOLS DISABLED`
- `Responseverbosity: minimal` inútil para lecturas — usar `full`
- `view_range` solo aplica a Text DAT, no Table DAT
- `replace_all_table` con `content=[[a,b],...]` reescribe el header
- `insert_row(row=N)` con N > Maxrows da error críptico — usar tool_td_mod

## Tool Manager

- Añadir slots: `Refreshtools.pulse()` + `Restartserver.pulse()`
- `server_state` JSON es la verdad, no el parámetro `Running`
- Save preset 2 veces rápido puede sobrescribir. Cambiar `Presetname` antes

## Tool VFS

- `Checkvfs.pulse()` con `Createifmissing=True` — sin esto el Agent reporta "no tools"

## Operadores TD genéricos

- `baseCOMP` no permite interacción de panel → usar `containerCOMP`
- DAT Execute con re-entrancia: `me.storage["processing"] = True`
- `webserverDAT.par.transparent` (minúscula)
- `parameterexecuteDAT.par.pars` (no `parameters`)
- Float custom pars con clampMin/clampMax: setear `.min` y `.max` explícitamente
- textDATs como callbacks: `language=python` explícito (default text, silent skip)

## webserverDAT headers

```python
response["Access-Control-Allow-Origin"] = "*"  # ✓
# response["headers"] = {"...": "..."}          # ✗ NO como sub-dict
```

## Regex en strings

Backslashes en triple-quoted strings se sobre-escapan. Usar raw strings.

## Numpy/torch ABI

Subir numpy o torch puede romper ABI con Resemblyzer, Silero VAD, etc. Actualizar torch/torchaudio juntos desde Python Manager.

## ⚠️ Callbacks de datexecuteDAT NO disparan desde el MCP

Cuando Claude hace `op(...).appendRow([...])` via MCP, la tabla se modifica pero los `datexecuteDAT` **NO reciben callbacks**. La mutación es real pero TD no la propaga.

Desde el runtime interno de TD sí funcionan normalmente.

**Síntoma:** testeas un watcher via MCP, no dispara, asumes que el código está mal. No lo está.

**Cómo testear correctamente:**
1. Llamar callback directamente: `mod._on_blast_complete(row_idx, log_dat)`
2. Disparar el evento desde dentro de TD, no desde el MCP
3. Verificar `dat.totalCooks` antes y después

Lo mismo aplica a `parameterexecuteDAT` — no confiar en que `par.X = valor` desde MCP dispare un parexec.

## me.storage para estado persistente en DAT executes

```python
# MAL: se resetea en cada recompilación
_PREV_ROWS = {}

# BIEN: persiste entre recompilaciones y con el .toe
def onTableChange(dat):
    key = "prev_rows__" + dat.path
    prev = me.fetch(key, None)
    cur = dat.numRows
    if prev is not None and cur > prev:
        pass  # procesar filas nuevas
    me.store(key, cur)
```

## ⚠️ me.storage + absTime.frame: timestamps que sobreviven al reinicio de TD

`me.storage` persiste con el `.toe` (se guarda y se recupera al reabrir). `absTime.frame` (o `me.time.frame`) es un contador de frames desde que arrancó el *proceso* de TD — se reinicia a un valor bajo cada vez que se abre TouchDesigner, sin relación con lo que haya guardado en `me.storage`.

Si guardas un `t_inicio = absTime.frame` para interpolar una animación (easing, slide, fade) y lo persistes en `me.storage`, y el `.toe` se guarda con esa animación a medias, al reabrir el proyecto — mismo PC o otro — el nuevo `absTime.frame` puede ser mucho menor que el `t_inicio` guardado. El cálculo de progreso (`t_raw = (ahora - t_inicio) / duracion`) sale muy negativo, y cualquier curva de easing no lineal (smoothstep, ease-in-out, etc.) que no esté pensada para inputs fuera de `[0, 1]` puede explotar a valores absurdos en vez de simplemente "no haber avanzado".

**Síntoma:** un parámetro (posición, escala, opacidad) se va a un valor astronómico o sin sentido justo después de reabrir el proyecto, de forma intermitente — solo cuando el `.toe` se guardó con una transición en curso. Fácil de confundir con un valor corrupto o un typo si no se mira `me.storage` directamente.

**Fix (patrón general):**

```python
def tick():
    ahora = absTime.frame
    info = me.fetch('mi_animacion', None)
    if info is None:
        return

    # Si 'ahora' es anterior a 't_inicio', el estado viene de una sesion
    # anterior de TD (el contador se reinicio). Resolver de inmediato
    # en vez de interpolar con un t_raw fuera de rango.
    if ahora < info['t_inicio']:
        t_raw = 1.0
    else:
        t_raw = (ahora - info['t_inicio']) / info['duracion']
    t_raw = max(0.0, min(1.0, t_raw))  # clamp defensivo, SIEMPRE

    # ... aplicar t_raw a la curva de easing que corresponda ...
```

Lo mismo aplica a cualquier "próximo evento programado" guardado como `absTime.frame + intervalo`: si al releerlo es mucho mayor que `ahora`, viene de una sesión anterior y hay que resincronizarlo — si no, el evento no vuelve a disparar nunca (parece "congelado" en vez de roto).

## ⚠️ webrenderTOP scroll: anti-patrones que NO funcionan

Cuando un `webrenderTOP` es el background de un `containerCOMP`, el scroll y los clicks NO se reenvían automáticamente al navegador CEF.

**Lo que NO funciona:**

- **`panelCHOP` + `chopexecuteDAT` calculando deltas del canal `wheel`**: el canal `wheel` es un pulso 0/1, no un float acumulativo. El delta siempre es ±1 y pierde la semántica de scroll.
- **Listeners JS tipo `addEventListener('wheel')` en el HTML**: no reciben eventos del container TD.
- **`sessionStorage` restore con `setTimeout` en el HTML**: lucha con el scroll del usuario y resetea la posición inesperadamente.
- **Confiar en que el container reenvía eventos al webrender por defecto**: no lo hace.

**Lo que SÍ funciona:** un `panelexecDAT` que vigila `lselect mselect rselect wheel insideu insidev` con `valuechange=True` y llama `web.interactMouse()` directamente. Ver snippet en td_snippets.md.
