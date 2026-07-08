# LOPs — Kits modulares con operadores `Any` portables

Patrones y trampas para construir un kit de tools MCP como conjunto de operadores
`Any` independientes agregados por un `tool_manager` — cada módulo activable,
portable entre proyectos (.tox), y con su skill de uso viajando dentro.

Descubierto/confirmado construyendo un kit real (jul 2026). Complementa
`lops_pitfalls.md` (parche `_dispatcher`, `Modulesmenu='(none)'`, `params` a
nivel de módulo — todo eso aplica aquí y no se repite).

**Última revisión:** 8 de julio de 2026.

---

## Patrón: nunca hardcodear la ruta del propio operador dentro del módulo

Dentro del módulo de un `Any` (cargado con `mod(dat)`), el global `me` es el
**DAT `module`**, no el COMP. Por tanto:

```python
def _me():
    return me.parent()        # el propio operador Any — portable

# Para strings de run() que necesitan ruta absoluta (ej. un watcher):
_SELF = me.parent().path      # evaluado al cargar el módulo, correcto por instancia
```

**Síntoma si se hardcodea** (`op('/mi_kit/mi_any')`): el módulo funciona hasta
que alguien copia el `.tox` a otro proyecto o renombra el operador — entonces
todos los handlers apuntan al operador viejo (o a `None`) sin error visible en
la carga.

Para referenciar recursos hermanos del kit (un DAT `session_id`, una tabla
compartida), resolver relativo al contenedor: `_me().parent().op(nombre)`, con
fallback a `op(valor)` si el parámetro trae ruta absoluta.

---

## ⚠️ Cambiar el `default` de un parámetro en `params` NO actualiza un parámetro ya creado

El framework del `Any` **preserva los valores** de los parámetros custom entre
`Reload`s (comportamiento deseable en general). Consecuencia: si cambias el
`default` de una entrada de `params` en el módulo y pulsas `Reload`, el
parámetro existente conserva su valor anterior — el `default` nuevo solo aplica
a instancias frescas del operador.

**Síntoma:** el código lee el parámetro esperando el default nuevo y recibe el
valor viejo; parece que el `Reload` "no funcionó".

**Fix:** tras cambiar un default en el módulo, asignar el valor explícitamente
una vez (`o.par.Nombre = valor_nuevo`) o borrar/recrear el operador.

---

## ✅ CONFIRMADO: `Outputmode='skills_config'` de `build_agent_skill` resuelve la portabilidad del skill

(Cierra el "pendiente de probar" de la sección Build Agent Skill de
`lops_pitfalls.md`.)

`_write_skills_config` escribe una **Table DAT `skills_config` DENTRO del
operador target** (columnas: `name, label, description, prompt_template,
tool_config`). Verificado empíricamente:

1. **Sobrevive al `Reload`** del `Any` (con `Modulesmenu='(none)'`).
2. **Viaja con el `.tox`** — `save()` + `loadTox()` del operador incluye la
   tabla con sus filas intactas.
3. **El Agent LOP la recoge automáticamente**: el `skill_manager` del agente
   escanea cada tool op de su secuencia buscando `tool_op.op('skills_config')`
   y registra cada fila como skill dinámico.

Limitación frente a `py_file`: una fila de `skills_config` no tiene función
`get_context()` — no hay `{live_state}`. Si el skill necesita estado en vivo,
o bien mantener la versión `.py` (no portable), o instruir al agente a
consultarlo con una tool (ej. "llama a X para ver el workflow cargado").

No dejar `{live_state}` en el `prompt_template` de un skills_config: no hay
nada que lo rellene.

---

## ⚠️ El scan de skills del Agent NO expande un `tool_manager` — solo mira sus tool ops directos

El `skill_manager` del Agent LOP itera `Tool{i}toolop` del propio agente y
busca `skills_config`/`GetSkills` **en esos operadores directamente**. Si el
slot apunta a un `tool_manager`, el scan mira el `tool_manager` (que no tiene
`skills_config`) y **no desciende** a los External Op Tools de su secuencia.
Existe `skill_manager.scan_tool_ops()` para eso, pero nada lo llama en el
AgentEXT actual.

**Implicación de arquitectura para kits modulares:**
- **Agente interno** (Agent LOP en el mismo proyecto): cablear los módulos
  `Any` directamente en la secuencia Tool del agente — así cada módulo trae
  sus tools Y su skill.
- **Cliente MCP externo** (Claude Desktop, móvil): el `tool_manager` agrega
  los mismos módulos y los expone por puerto. Los skills no viajan por MCP —
  la guía de uso para clientes externos va en las descriptions de las tools.

Ambas vías coexisten sobre los mismos operadores módulo sin duplicar nada.

---

## ⚠️ Los handlers que delegan en un módulo de otro proyecto se pudren en silencio

Un `Any` cuyo handler hace `op('/otro/proyecto/modulo').module.funcion(...)`
depende de que esa función siga existiendo con ese nombre exacto. Confirmado
en un caso real: el módulo de destino renombró funciones públicas a privadas
(prefijo `_`) y una función desapareció en una variante del proyecto — tres
tools del kit quedaron rotas **sin ningún error hasta el momento de la
invocación** (el `Any` carga bien, `get_tools()` las lista, el fallo solo
aparece al llamarlas: `AttributeError`).

**Reglas:**
- Para módulos portables, preferir implementación nativa dentro del propio
  módulo cuando la lógica sea pequeña (control de un bridge HTTP, appendRow a
  una tabla, secuencia de pulses de un TTS) — la dependencia externa solo para
  lógica genuinamente grande (generación de informes, etc.).
- Si se delega: envolver en `try/except` devolviendo `{ok: False, error}` y,
  al probar el kit, invocar **cada** handler de verdad contra la instancia
  viva — no asumir que "compila = funciona". Un `getattr(mod, 'fn', None) or
  getattr(mod, '_fn', None)` tolera el patrón público→privado.

---

## ⚠️ Scoping del exec de `network_context`/`td_code`: funciones anidadas y comprehensions no ven los nombres de fuera

El código de estas tools se ejecuta con globals/locals separados. Consecuencia:
una función definida en la llamada **no ve** clases/variables definidas en la
misma llamada (`NameError`), y una list/dict-comprehension **no ve** variables
locales del script (`NameError` dentro del listcomp).

```python
# FALLA: helper anidado no ve MTC
class MTC: ...
def call(...):
    m = MTC(...)   # NameError: MTC

# FALLA: listcomp no ve 'tbl'
row = [tbl[r, c].val for c in range(tbl.numCols)]   # NameError: tbl
```

**Fix:** escribir el script plano — bucles `for` normales en vez de
comprehensions que referencien locals, y sin funciones/clases auxiliares
(inline con `types.SimpleNamespace` para mocks).

---

## Patrón: probar un handler de `Any` sin cliente MCP (sin clases)

Por el problema de scoping de arriba, el mock clásico con clases falla en
`network_context`. Versión que funciona:

```python
import json
from types import SimpleNamespace
m = SimpleNamespace(function=SimpleNamespace(arguments=json.dumps({"arg": "valor"})))
r = op('/kit/mi_any').ext.AnyExt._call('handle_mi_tool', m)
```

---

## Patrón: watcher de job async en un módulo de `Any`

Para esperar un resultado de un proceso externo (`Popen`) sin bloquear:

```python
_SELF = me.parent().path   # a nivel de módulo

def _watcher(slug, out_dir, row_idx, elapsed=0):
    # ... comprobar disco/tabla; si listo, finalizar y return ...
    nxt = ("op('" + _SELF + "').ext.AnyExt._module._watcher("
           + repr(slug) + ", " + repr(out_dir) + ", " + str(row_idx)
           + ", " + str(elapsed + 2) + ")")
    run(nxt, delayFrames=120)   # se re-programa desde el cook thread
```

Claves: `ext.AnyExt._module` (en un `Any` no existe `.module`, ver
`lops_pitfalls.md`), `Popen` sin `join`, timeout configurable por parámetro
(GPU bajo contención multiplica los tiempos), y una comprobación por tick —
nunca `time.sleep()`.
