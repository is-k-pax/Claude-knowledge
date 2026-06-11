# TouchDesigner — Crear tools para agentes LOPs

Como crear, conectar y testear tools nuevos para Agent LOPs.

**Ultima revision:** junio 2026.

---

## Tabla de decision: que tipo de tool usar

| Situacion | Tool recomendado |
|---|---|
| Leer / escribir una tabla o texto DAT, logica simple | Tool DAT (tool_datLOP) |
| Validacion compleja, errores semanticos en lenguaje natural, multiples funciones | Tool TD Mod (tool_td_modLOP) — recomendado |
| Controlar parametros de un operador (volume, color, posicion) | Tool Parameter LOP |
| Llamar a un servicio HTTP externo (imagen, voz, API externa) | Tool Request LOP |
| Inspeccion amplia del proyecto, tareas de desarrollo ad-hoc | Tool TD Code — solo agentes de desarrollo |

**Regla general:** si necesitas validar argumentos antes de tocar nada, dar mensajes de
error legibles, o agrupar varias operaciones en un solo slot del agente, usa Tool TD Mod.
Tool DAT es mas simple pero sus errores son crípticos y cada instancia ocupa un slot.

---

## Paso a paso: Tool TD Mod

### 1. Estructura de una funcion de modulo

```python
def mi_funcion(arg1: str, arg2: int = 0) -> dict:
    """Descripcion breve que el agente lee.

    Args:
        arg1: descripcion. Valores validos: "opcion_a", "opcion_b".
        arg2: descripcion. Default 0.

    Returns:
        dict con ok (bool) y resultado o error (str).
    """
    # Validacion al inicio — el agente recibe el error antes de tocar nada
    if arg1 not in ("opcion_a", "opcion_b"):
        return {"ok": False, "error": f"arg1 invalido: {arg1}. Usa opcion_a|opcion_b"}
    if arg2 < 0:
        return {"ok": False, "error": "arg2 debe ser >= 0"}

    # logica
    resultado = f"procesado {arg1} con arg2={arg2}"
    return {"ok": True, "resultado": resultado}
```

Reglas del modulo:
- Siempre retornar dict con clave `ok` (bool)
- Validar argumentos al principio, antes de cualquier efecto secundario
- Docstring obligatorio: el agente lo lee con `action="doc"` antes de llamar
- Tipos anotados en la firma: el agente los usa para construir los argumentos

### 2. Deploy del modulo en TD

```python
src_code = '''
# pegar aqui el codigo del modulo
'''

# Verificar sintaxis antes de crear el DAT
compile(src_code, 'mi_modulo', 'exec')

# Crear o actualizar en el comp modules del tool_td_mod
modules_comp = op('/project1/tool_td_mod1/modules')
existing = modules_comp.op('td_mi_modulo')
if existing:
    existing.text = src_code
else:
    dat = modules_comp.create(textDAT, 'td_mi_modulo')
    dat.text = src_code
```

Convencion de nombres: el DAT se llama `td_<nombre>`. Si `Stripmodprefix = True` en el
operador, el agente lo ve como modulo `<nombre>` (sin el prefijo td_).

### 3. Verificar que el modulo esta expuesto

```python
schema = op('/project1/tool_td_mod1').GetTool()
print(schema['tool_definition']['function']['parameters']['properties']['args']['description'])
# Debe mostrar la lista de modulos y funciones disponibles
```

---

## Paso a paso: Tool DAT

### 1. Crear y configurar el operador

- Crear el operador `tool_datLOP` en `/project1`
- Parametro `Target`: apuntar al DAT que la herramienta puede leer/escribir
- Parametro `Preset`: `read_only`, `append_only`, o `custom`
- Parametro `Toolname`: **CRITICO — debe ser unico entre todos los Tool DAT del mismo agente**
  - Default es `edit_td_dat` — cambiarlo siempre
  - Si dos Tool DAT tienen el mismo Toolname: `DUPLICATE TOOL — ALL TOOLS DISABLED`
- Parametro `Responseverbosity`:
  - `full` para tools de lectura (el agente necesita ver el contenido)
  - `minimal` para tools de escritura (solo confirma exito/fallo)

### 2. Sub-operaciones disponibles

El agente ve las operaciones con el prefijo del Toolname: `<Toolname>_read_content`,
`<Toolname>_append_row`, `<Toolname>_replace_all_table`, `<Toolname>_insert_row`,
`<Toolname>_delete_row`. Configurar el Preset para exponer solo las necesarias.

---

## Conectar un tool a un Agent

### Anadir un slot

```python
ag = op('/project1/agent_XXX')

# Ampliar la sequence (no asignar ag.par.Tool.val directamente)
ag.par.Tool.sequence.numBlocks = ag.par.Tool.sequence.numBlocks + 1
slot = ag.par.Tool.sequence.numBlocks - 1

# Asignar el operador y activarlo
getattr(ag.par, f'Tool{slot}toolop').val = '/project1/mi_tool'
getattr(ag.par, f'Tool{slot}toolactive').val = 'on'
```

### Forzar re-parse (SIEMPRE tras cambios en la sequence)

```python
ag.par.reinitextensions.pulse()
# El log debe mostrar: "Parsed N tools from M blocks"
# Si no aparece ese mensaje, el agente no ha registrado el cambio
```

---

## Testear un tool sin agente (MockToolCall)

Permite verificar que el tool funciona correctamente sin gastar tokens ni esperar respuesta
del LLM. Util para validar logica, mensajes de error y formato de respuesta.

### Para Tool TD Mod

```python
import json
tdm = op('/project1/tool_td_mod1')

class MockToolCall:
    def __init__(self, args):
        class _F:
            def __init__(self, a): self.arguments = json.dumps(a)
        self.function = _F(args)

# Listar modulos disponibles
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({"action": "list"})))

# Ver docstring de un modulo
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action": "doc",
    "module": "mi_modulo"
})))

# Llamar una funcion y ver el resultado
result = tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action": "call",
    "function": "mi_modulo.mi_funcion",
    "args": {"arg1": "opcion_a", "arg2": 3}
}))
print(json.dumps(result, indent=2, default=str))
```

### Para Tool DAT

```python
# Leer el schema que ve el agente
tool = op('/project1/mi_tool_dat')
print(tool.GetTool())

# Verificar que el Toolname no colisiona con otros Tool DAT del agente
ag = op('/project1/agent_XXX')
n = ag.par.Tool.sequence.numBlocks
toolnames = []
for i in range(n):
    t = getattr(ag.par, f'Tool{i}toolop').eval()
    if t:
        schema = t.GetTool()
        if isinstance(schema, list):
            for s in schema:
                toolnames.append(s.get('tool_definition',{}).get('function',{}).get('name','?'))
        elif isinstance(schema, dict):
            toolnames.append(schema.get('tool_definition',{}).get('function',{}).get('name','?'))
print("Tools registrados:", toolnames)
dupes = [x for x in toolnames if toolnames.count(x) > 1]
if dupes:
    print("COLISION DETECTADA:", set(dupes))
else:
    print("Sin colisiones")
```
