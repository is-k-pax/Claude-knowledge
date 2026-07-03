# LOPs — Snippets reutilizables

Código reutilizable para tareas comunes con LOPs.

**Última revisión:** julio 2026.

---

## Crear tools dedicadas con el operador Any

> ⚠️ Antes de usar: verificar que `AnyExt` tiene el parche de `_dispatcher()` (ver lops_pitfalls.md).
> Sin él las tools se registran pero no se ejecutan.

**Cuándo:** necesitas tools con schemas propios (nombre, parámetros tipados) en vez de un genérico "ejecuta Python". Ideal para Tool Manager → Claude Desktop / MCP.

**Patrón:** copiar el operador `Any` desde `/dot_lops/custom_operators/any`, escribir un módulo Python en su DAT `module`, y apuntar `Moduledat` → `./module`.

```python
# Estructura del módulo (texto completo del DAT 'module'):
import json

name = "mi_modulo"
description = "Descripción corta"
category = "tool"
params = []  # custom UI pars si necesitas

def get_tools(ext):
    """ext = AnyExt instance. Devuelve lista de dicts con tool definitions."""
    return [
        {
            "name": "mi_tool",
            "description": "Qué hace esta tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."},
                    "param2": {"type": "number", "description": "..."}
                },
                "required": ["param1"]
            }
        }
    ]

def handle_mi_tool(ext, tool_call):
    """Handler: ext = AnyExt, tool_call.function.arguments = JSON string."""
    args = json.loads(tool_call.function.arguments)
    p1 = args['param1']
    # ... lógica con op() ...
    return {"status": "success", "message": f"Done: {p1}"}
```

**Setup después de escribir el módulo:**
```python
at = op('/ruta/al/any_operator')
at.par.Moduledat = './module'
at.par.Reload.pulse()
# Verificar: at.GetTool() → lista de tool dicts
```

**Conectar al Tool Manager:**
```python
tm = op('/ruta/tool_manager1')
slot_pars = [p for p in tm.pars('Tool0op')]
slot_pars[0].val = at
tm.par.Refreshtools.pulse()
# Después: tm.par.Restartserver.pulse() o Startserver.pulse()
```

**Protocolo GetTool — formato devuelto por el Any:**
```python
{
    'tool_definition': {
        'type': 'function',
        'function': {
            'name': 'tool_name',
            'description': '...',
            'parameters': { ... JSON Schema ... }
        }
    },
    'callback_info': {
        'handler': <callable>,
        'response_format': 'json'
    }
}
```

Convención de handler: `handle_{tool_name}(ext, tool_call)`.
El handler siempre recibe `ext` (AnyExt) como primer arg.

---

## Motor de animación de un solo GLSL TOP, controlado por un agente (multi-modo, barato en tokens)

**Cuándo:** un agente (Claude vía tool_agent) tiene que controlar algo que se anima con el tiempo
(luces, visuales, cualquier cosa con movimiento) y NO debe implementar el loop de animación él mismo
llamando tools repetidamente. El agente da una orden (modo + velocidad + colores), TD anima solo a
framerate. Añadir un modo nuevo es añadir un `else if` al shader — no rehacer la arquitectura.

**Por qué importa para el coste de tokens:** una vez el shader está escrito, pedir "luz calmada
verde" o "neón rojo y azul, movimiento lento" son 2-4 llamadas de tool que solo cambian uniforms
ya existentes — cero GLSL nuevo, cero tokens en reescribir shader. Solo hace falta tocar el shader
si se pide un patrón visual que no está entre los modos ya implementados.

**Patrón — 3 piezas:**

1. **Un GLSL TOP con los modos empaquetados en un `vec4` uniform** (mode, speed/phase, intensity, unused) en vez de uniforms sueltos — así solo hace falta un bloque en la página Vectors del GLSL TOP:
```glsl
uniform vec4 uColor1;
uniform vec4 uColor2;
uniform vec4 uParams; // x=mode, y=speed/phase, z=intensity, w=unused

layout(location = 0) out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    int mode = int(uParams.x);
    float speed = uParams.y;
    vec3 col = uColor1.rgb;

    if (mode == 0) col = uColor1.rgb;                              // solid
    else if (mode == 1) col = fract(speed) < 0.5 ? uColor1.rgb : vec3(0.0);  // blink
    else if (mode == 2) col = uColor1.rgb * speed;                 // pulse (speed ya es 0-1 desde CPU)
    else if (mode == 3) {                                          // gradient estático
        float f = clamp((uv.x + uv.y) * 0.5, 0.0, 1.0);
        col = mix(uColor1.rgb, uColor2.rgb, f);
    }
    else if (mode == 4) {                                          // rainbow
        float hue = fract(uv.x + uv.y + speed);
        col = TDHSVToRGB(vec3(hue, 1.0, 1.0));
    }
    else if (mode == 6) {                                          // noise orgánico
        float n = TDSimplexNoise(vec3(uv * 3.0, speed)) * 0.5 + 0.5;
        col = mix(uColor1.rgb, uColor2.rgb, n);
    }

    col *= uParams.z;  // intensity
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
```

2. **Asignar uniforms del GLSL TOP por código** (Colors page para vec4 con nombre de color, Vectors page para vec4 genérico):
```python
glsl = dmx.create(glslTOP, 'led_engine')
glsl.par.pixeldat = pixel_dat  # DAT con el shader de arriba
glsl.par.outputresolution = 'custom'
glsl.par.resolutionw = 64
glsl.par.resolutionh = 64      # cuadrado si el POP de destino tiene escala 1:1 (ver lookuptex más abajo)

glsl.par.color.sequence.numBlocks = 2
glsl.par.color0name = 'uColor1'
glsl.par.color1name = 'uColor2'
glsl.par.vec0name = 'uParams'
glsl.par.vec0valuex = 0    # mode
glsl.par.vec0valuez = 1.0  # intensity
glsl.cook(force=True)
print(glsl.warnings())  # vacío = todos los uniforms asignados correctamente
```

3. **La animación corre sola vía expresión TD, no vía Python del agente.** Guardar la "velocidad" en `storage` del propio operador, y que el parámetro de fase sea una expresión que multiplica esa velocidad por `absTime.seconds`:
```python
glsl.store('rate', 0.0)
glsl.par.vec0valuey.expr = "op('.').fetch('rate', 0.0) * absTime.seconds"
glsl.par.vec0valuey.mode = ParMode.EXPRESSION
```
El handler de la tool del agente solo hace `glsl.store('rate', speed)` — TD calcula el resto cada frame sin más llamadas.

**Nota sobre geometría:** si el TOP alimenta un `lookuptex POP` que usa `P(0)`/`P(1)` normalizados
como UV (patrón común para tiras LED con Point POPs), la resolución del GLSL TOP debe coincidir con
la forma real de la geometría (cuadrada si la escala del POP es 1:1, rectangular si no) — un TOP
1×N (tipo "tira") solo es correcto si los puntos están dispuestos linealmente en un eje.

---

## Listar todos los tools que ve un agente

**Cuándo:** al entrar a un proyecto desconocido, o para verificar que tools tiene parseadas un Agent LOP tras cambios en su Tool sequence.

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

## Tester de función de módulo en tool_td_mod (sin agente)

**Cuándo:** para testear una función de un módulo Python en tool_td_mod sin lanzar un agente real (sin coste, sin espera).

```python
import json
tdm = op('/project1/tool_td_mod1')

class MockToolCall:
    def __init__(self, args):
        class _F:
            def __init__(self, a): self.arguments = json.dumps(a)
        self.function = _F(args)

# Listar módulos disponibles
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({"action":"list"})))

# Llamar una función concreta
result = tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action":"call",
    "function":"<modulo>.<funcion>",
    "args": {"arg1": "valor1"}
}))
print(json.dumps(result, indent=2, default=str))
```

---

## Reset de sesión de un agente sin perder configuración

**Cuándo:** cuando quieres empezar una conversación limpia con el mismo agente (mismos tools, mismo system_message) sin borrar ni reconfigurar nada.

```python
ag = op('/project1/agent_XXX')
ag.par.Cancelcall.pulse()
ag.par.Clearsession.pulse()
ag.par.reinitextensions.pulse()
# Resultado: conversación vacía, mismos tools y system_message
```

---

## Cost guard antes de probar nada

**Cuándo:** siempre que vayas a lanzar queries de prueba. Pone un tope de gasto duro para que una llamada no se desmande.

```python
ag = op('/project1/agent_test')
ag.par.Costbudget = 0.05  # 5 céntimos máximo por query
ag.par.Resetcostmeter.pulse()
# Lanza query; si supera $0.05 el agente corta automáticamente
```

---

## Buscar logs útiles de un operador

**Cuándo:** para diagnosticar qué ha pasado en un LOP. Cada LOP suele tener un sub-DAT logs con eventos timestampados.

```python
log = op('/project1/<op>/logs')
print(f"{log.numRows} entries")
for r in range(max(1, log.numRows-10), log.numRows):
    print([str(log[r,c].val)[:120] for c in range(min(4, log.numCols))])
```

---

## Crear un módulo Python para tool_td_mod desde cero

**Cuándo:** cuando quieres añadir una nueva función al repertorio del agente a través de tool_td_mod, siguiendo el patrón de módulo documentado y tipado.

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

**Cuándo:** para LOPs con bridges o conexiones externas (claude_codeLOP, MCP servers, sockets) que no se conectan solos al cargar el proyecto. Un executeDAT con start=True lanza el handshake automáticamente. Es idempotente: si ya está conectado, el pulse no hace nada.

```python
s = op('/project1').create(executeDAT, 'startup_<servicio>')
s.par.language = 'python'
s.par.start = True   # CRÍTICO: dispara onStart al cargar el .toe
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

---

## Watcher event-driven sobre un DAT de log

**Cuándo:** para vigilar una tabla que crece monotónicamente (como un log) y reaccionar SOLO a filas nuevas que cumplan un criterio. Usa me.storage para persistir el estado entre disparos.

> ATENCIÓN al testear: los appendRow desde el MCP no disparan los callbacks de este watcher
> (ver lops_pitfalls.md sección callbacks datexecuteDAT). Para validar, lanza una operación
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

# Inicializar contador para no procesar el histórico existente
target = op(w.par.dat.eval())
w.store('prev_rows__' + target.path, target.numRows)
```

---

## Escalar y codificar una imagen para respuesta MCP a un cliente móvil

**Cuándo:** un tool MCP necesita devolver una imagen a un cliente que la va a mostrar en pantalla pequeña (Claude Desktop en móvil, apps de mensajería). Descargar la imagen original (varios MB) y dejar que el modelo la convierta a base64 es lento y gasta tokens de más. Escalar antes de codificar reduce el payload a 30-150 KB.

**Requiere:** Pillow (`from PIL import Image`) en el Python de TD — normalmente ya viene incluido; verificar con `from PIL import Image; print(Image.__version__)`.

```python
import io
import base64
import urllib.request
from PIL import Image

def url_to_mobile_b64(url, max_dim=1024, quality=85):
    """Descarga una URL, escala con Pillow y devuelve JPEG en base64.
    max_dim es el mayor de ancho o alto. quality 1-95.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "TD-LOPs/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim))  # mantiene aspect ratio, no agranda
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")
```

**En el handler de la tool:**
```python
def handle_enviar_imagen_movil(ext, tool_call):
    args = json.loads(tool_call.function.arguments)
    url = args.get("url", "")
    if not url:
        return {"ok": False, "error": "url vacia"}
    try:
        b64 = url_to_mobile_b64(url, max_dim=args.get("max_dim", 1024),
                                 quality=args.get("quality", 85))
        return {"ok": True, "base64": b64, "media_type": "image/jpeg",
                "approx_kb": round(len(b64) * 0.75 / 1024, 1)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

**Valores de referencia:** `max_dim=1024, quality=85` → 100-250 KB para fotos normales. `max_dim=512, quality=75-80` → 20-50 KB, suficiente para miniaturas de galería. Bajar `max_dim` primero si el payload sigue siendo grande; `quality` tiene menos impacto en el tamaño que la resolución.

**Reutilizable también para escalar salida de un TOP interno** (en vez de una URL externa): sustituir la descarga por `top.save(temp_path, quality=quality)` o usar `top.numpyArray()` → `Image.fromarray()` si se quiere evitar el archivo temporal.
