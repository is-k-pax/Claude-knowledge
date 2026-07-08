# LOPs — Pitfalls acumulados (parte 2)

Continuación de `lops_pitfalls.md` (el archivo original supera el tamaño cómodo
de edición segura vía MCP — los pitfalls nuevos van aquí).

**Última revisión:** 8 de julio de 2026.

---

## Build Agent Skill — `Outputmode='skills_config'` SÍ resuelve la portabilidad del skill (confirmado)

La duda pendiente documentada en la parte 1 ("el nivel Project .lops no viaja con el `.tox`")
queda resuelta. `Outputmode='skills_config'` escribe el skill en una **Table DAT llamada
`skills_config` DENTRO del operador target** (columnas: `name, label, description,
prompt_template, tool_config`). Verificado empíricamente:

- **Sobrevive al `Reload` del `Any`** (con `Modulesmenu='(none)'`).
- **Viaja con el `.tox`**: `save()` + `loadTox()` del operador reproduce la tabla con el skill intacto.
- **El Agent LOP lo registra solo**: el `skill_manager` del agente escanea cada operador de su
  secuencia de tools buscando una tabla `skills_config` y registra sus filas como skills dinámicos
  — sin tocar carpetas `.lops/skills/` ni el system message.

Escritura programática (sin pasar por la UI):
```python
bs = op('/ruta/build_skill1')
skill_data = {"name": "...", "label": "...", "description": "...",
              "prompt_template": "...", "tool_config": ""}
bs.ext.SkillBuilderExt._write_skills_config(skill_data, op('/ruta/al/target'))
```

### Matiz: `{live_state}` renderiza VACÍO en un `Any` — usar `{tool_config}` en su lugar

Para skills de `skills_config`, `{live_state}` se rellena llamando a `GatherSkillContext()`
en las extensiones del operador target — y `AnyExt` **no implementa ese método**, así que
queda vacío (sin error). Placeholders que SÍ funcionan en un `Any`:

- `{tool_name}` / `{tool_description}` — de la primera tool de `GetTool()`.
- `{tool_config}` — snapshot en vivo de los parámetros listados en la columna `tool_config`
  (JSON dict `{"NombrePar": ""}`); el skill_manager los evalúa en el momento de activar el skill.

**Trade-off `py_file` vs `skills_config`:** un skill `py_file` puede llevar `get_context()`
con lógica Python arbitraria para el estado en vivo (ej. leer el workflow cargado de OTRO
operador), pero vive en `.lops/skills/` junto al `.toe` y no viaja con el `.tox`. Un skill
`skills_config` viaja con el operador pero su estado en vivo se limita a `{tool_config}`
(parámetros del propio operador). Elegir según qué pese más en cada caso.

### Nota relacionada: `build_agent_profile` para configs de agente por despliegue

Operador hermano que guarda la configuración de un Agent (parámetros cambiados + secuencia
de tools + system prompt) como JSON reutilizable/apilable. Complementa lo anterior: los skills
viajan con cada tool op; el profile captura el agente. Ojo: mismo problema de ubicación
(carpeta user o `.lops/agent_profiles` del proyecto), y los paths absolutos fuera del agente
se guardan pero marcados como warning de portabilidad.

---

## ⚠️ `Modulesmenu` puede REVERTIR a un módulo starter tras un `Reload` — re-verificarlo, no fiarse de haberlo puesto a `(none)` una vez

**Síntoma:** se pone `Modulesmenu='(none)'` en un `Any` recién clonado, se trabaja con él
(escritura de módulo, varios `Reload`), y al revisarlo más tarde `Modulesmenu` vuelve a mostrar
un valor starter (`preset_morpher`, `text_editor`...). En el caso observado el módulo custom
NO se machacó (probablemente porque `Moduledat` apuntaba explícitamente al DAT `./module`
custom), pero el estado es el mismo que el del pitfall de sobreescritura de la parte 1 — una
bomba de relojería.

**Regla:** tras cualquier tanda de `Reload`/`reinitextensions` sobre un `Any` con módulo
custom, re-verificar `Modulesmenu == '(none)'` y volver a asignarlo si revirtió. Verificar
también la integridad del módulo (buscar una firma propia en el `.text`, ej. el nombre de un
handler) en vez de asumir que sigue intacto.

---

## ⚠️ Cambiar el `default` de un parámetro en `params` del módulo NO actualiza un parámetro ya creado

**Síntoma:** se edita la lista `params` del módulo de un `Any` cambiando el `default` de un
parámetro existente, se pulsa `Reload`, y el parámetro sigue con el valor anterior.

**Causa:** el framework preserva deliberadamente los VALORES de los parámetros que ya existen
al recargar (para no machacar configuración del usuario). El `default` solo aplica al CREAR el
parámetro por primera vez.

**Fix:** tras cambiar un default en el módulo, asignar el valor explícitamente una vez
(`o.par.Nombre = nuevo_valor`) o borrar/recrear el parámetro. No asumir que Reload lo actualiza.

---

## ⚠️ Dentro del módulo de un `Any`, `me` es el DAT `module` — usar `me.parent()` para autorreferencia portable

El módulo se carga con `mod(dat)`, así que `me` a nivel de módulo apunta al propio DAT
`module`. Para referenciar el operador `Any` contenedor sin hardcodear su path:

```python
def _me():
    return me.parent()          # el Any
# contenedor del kit (hermanos, tablas compartidas):
_kit = me.parent().parent()
# path absoluto capturado al cargar (para strings de run()):
_SELF = me.parent().path
```

Hardcodear `op('/mi_container/mi_any')` dentro del módulo rompe la portabilidad al copiar el
`.tox` a otro proyecto o al renombrar el operador — el patrón `me.parent()` sobrevive a ambos.

---

## ⚠️ En `network_context`/`td_code`, funciones anidadas y comprehensions NO ven las variables del script

**Síntoma:** `NameError` sobre una variable/clase claramente definida unas líneas antes,
pero solo cuando se referencia desde dentro de una función definida en el mismo script, una
clase anidada, o una list/dict comprehension.

**Causa:** el código se ejecuta con `exec()` usando diccionarios de globals/locals separados —
las definiciones del script van a *locals*, pero las funciones anidadas y las comprehensions
resuelven nombres libres contra *globals*. Es el comportamiento estándar de `exec` en Python,
no un bug del tool.

**Fix:** en estos tools, escribir todo plano — bucles `for` en vez de comprehensions que
referencien variables del script, y nada de funciones helper que capturen estado del script.
`from types import SimpleNamespace` para mocks en vez de definir clases.

```python
# MAL (NameError en la comprehension):
cols = [tbl[0, c].val for c in range(tbl.numCols)]
# BIEN:
cols = []
for c in range(tbl.numCols):
    cols.append(tbl[0, c].val)
```

---

## ⚠️ Si `read`/`edit_td_dat_*` fallan con "Handler method not found: dispatch", el `any1` del tool manager de desarrollo perdió el parche del dispatcher

**Síntoma:** las tools de edición/lectura de DATs del Tool Manager de desarrollo fallan con
`Handler method not found: dispatch in .../any1`, y `td_code` puede fallar genéricamente a la vez.

**Causa:** el `any1` interno del tool manager de desarrollo es un operador `Any` normal y
necesita el mismo parche de `_dispatcher()` documentado en la parte 1. El parche puede perderse
(actualización de LOPs, restauración del operador, etc.).

**Fix:** aplicar el parche estándar de `_dispatcher()` al `AnyExt` de ese `any1` +
`reinitextensions.pulse()` + `Refreshtools.pulse()` en su tool_manager. Verificado: restaura
`read`/`edit_td_dat_*` en caliente sin reiniciar el servidor (reiniciarlo cortaría la propia
conexión MCP desde la que se está trabajando). `td_code` puede requerir diagnóstico aparte
(vive en `tool_td_code1`, no en `any1`).

---

## ⚠️ Los wrappers que delegan en un módulo externo se pudren en silencio — verificar contra la instancia viva, no contra la doc

**Caso real:** un `Any` exponía 20 tools cuyos handlers delegaban en funciones de un módulo de
otro container (`_tg().hablar(...)`, `_th()._escena(...)`). Con el tiempo, en ese módulo:
algunas funciones se renombraron con prefijo `_` (privatizadas), otras se eliminaron, y en otra
versión del proyecto los prefijos eran los contrarios. Resultado: varias tools llevaban tiempo
rotas (`AttributeError` solo al invocarlas) sin que nada lo señalara — la lista de tools seguía
publicándose perfecta en el MCP.

**Reglas:**
- Antes de dar por buena una tool que delega, invocarla de verdad (mock de `tool_call` +
  `ext.AnyExt._call(...)`) contra la instancia viva — no basta con que el schema aparezca.
- Al delegar en funciones que pueden cambiar de nombre/visibilidad, resolver con fallback:
  `fn = getattr(mod, 'contexto', None) or getattr(mod, '_contexto', None)` y devolver un error
  explicativo si no existe.
- Mejor aún: si la lógica es pequeña (una secuencia de pulses, un `requests.put`), portarla
  nativa al módulo con sus dependencias como parámetros de Config — elimina la clase entera
  de fallo.
