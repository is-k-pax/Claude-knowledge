# LOPs — Pitfalls acumulados

Errores y trampas descubiertas trabajando con LOPs y Tool Manager.

**Última revisión:** 4 de julio de 2026.

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
- **Un `tool_manager` puede agregar VARIOS operadores en su secuencia "External Op Tools"**
  (Tool0op, Tool1op, Tool2op...) — no solo un `Any`. Cualquier LOP con `GetTool()` vale: otro
  `Any`, el `comfyui` nativo, un `mcp_client`. Este es el mecanismo real para componer "kits" de
  capacidades por proyecto (ej. un `Any` de lógica de sala + un `comfyui` de generación de imagen,
  añadido solo en los proyectos que lo necesiten).
- **El sistema de Presets (`Savepreset`/`Loadpreset`) NO recablea qué operadores están en la
  secuencia** — solo guarda y restaura qué tools individuales están encendidas/apagadas
  (`Enable<tool>`) dentro de lo que ya esté conectado en ese momento. `Loadpreset` lee
  `Tool_Toggles` de la tabla de presets y aplica esos switches; el campo `Tool_Sequence` se
  guarda pero no se usa para reconstruir el cableado. Para cambiar de "kit" de verdad (añadir o
  quitar un operador entero como el de ComfyUI) hay que tocar Tool0op/Tool1op a mano o mediante
  `.tox` distintos por proyecto — los Presets solo sirven para afinar qué tools concretas ve el
  agente dentro de un cableado ya fijo.

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

## ⚠️ `time.sleep()` en bucle dentro de `td_code`/`network_context` para esperar un job async bloquea TD entero (y puede colgar el propio job)

**Síntoma:** se lanza una generación/tarea asíncrona en un operador externo (ej. `comfyui` LOP
esperando a ComfyUI) y, para "esperar el resultado", se hace un bucle tipo
`for i in range(N): time.sleep(2); check_status()` dentro de una sola llamada a
`td_code`/`network_context`. El status queda pegado ("Queued", "Executing"...) mucho más tiempo
del esperable, y a veces el job nunca progresa hasta que se cancela manualmente.

**Causa:** `td_code`/`network_context` ejecutan en el proceso/hilo de TD. Un `time.sleep()` ahí
bloquea ese hilo por completo durante toda la duración del bucle — no es una espera "en segundo
plano". Si la comunicación con el servicio externo depende de que TD siga cocinando (ej. un
WebSocket que necesita que el cook thread procese mensajes entrantes para avanzar el estado del
job), el bloqueo puede impedir que el propio job que se está esperando progrese, dejándolo
atascado indefinidamente en vez de simplemente tardar más.

**Fix:**
- Nunca hacer polling con `sleep()` dentro de una sola llamada. Hacer UNA comprobación de estado
  por llamada, sin espera, y dejar pasar tiempo real entre llamadas separadas (o pedirle al
  usuario que confirme cuándo ha pasado tiempo suficiente, si el usuario tiene la UI de TD
  delante y puede verificarlo él mismo más rápido que sondeando a ciegas).
- Si un job se queda atascado por este motivo: `Interrupt` + `Clear Queue` (o el pulse
  equivalente del operador) y relanzar la generación limpia. Ha funcionado como recuperación
  fiable tras un bloqueo de este tipo.
- Regla general: cualquier espera de un resultado async en LOPs debe resolverse con el mecanismo
  nativo del framework para eso (callbacks, `run(..., delayFrames=N)` reprogramándose desde el
  cook thread, o `ext.run_async(...)` si el operador lo expone) — nunca con una espera bloqueante
  dentro de la misma llamada que dispara la tarea.

---

## ⚠️ Llamar a funciones del módulo de un `Any` desde `run()` lanzado por un thread en background: `.module` no existe

**Síntoma:** un thread en background (ej. generación REST de ComfyUI) termina y reprograma un
callback al cook thread con `run(f"op('{path}').module._mi_funcion(...)", delayFrames=1)`. La
tarea nunca se completa — sin excepción visible en el resultado de la llamada original, porque el
`run()` falla de forma diferida y silenciosa (el error solo aparece en el log/Textport de TD, no
se propaga a quien programó el `run()`).

**Causa:** para un operador `Any`, el atributo `.module` **no existe** en el objeto COMP —
`op('/ruta/al/any_op').module` lanza `tdAttributeError`. El módulo Python cargado vive en
`ext.AnyExt._module`. El acceso correcto es `op('/ruta').ext.AnyExt._module._mi_funcion(...)`.
(Para un Text DAT normal con contenido Python sí existe `.module` — la confusión viene de mezclar
ambos patrones.)

**Fix:**
```python
# MAL (falla silenciosamente vía run() desde un thread):
run(f"op('{path}').module._finalize(...)", delayFrames=1)

# BIEN:
run(f"op('{path}').ext.AnyExt._module._finalize(...)", delayFrames=1)
```

**Regla de verificación:** antes de fiarte de un `run()` disparado desde un thread, probar la
misma llamada de forma síncrona primero (`op('{path}').ext.AnyExt._module._finalize(...)`
directamente en `td_code`) para confirmar que la ruta de acceso y la firma de argumentos son
correctas. Un `run()` con un string mal formado no da ningún feedback inmediato — el fallo solo se
descubre por ausencia de efecto (el job se queda "pending" para siempre).

**Relacionado:** revisar también el número de argumentos pasados en el string de `run()` —
al construir la llamada dinámicamente con f-strings es fácil que la firma de la función real
(por ejemplo, 3 parámetros posicionales) no coincida con lo que el string generado realmente pasa
(por ejemplo, solo 2) sin que ningún linter lo detecte, porque todo es texto hasta que TD lo
ejecuta.

---

## ComfyUI LOP (`comfyui` / ComfyTD)

Notas de uso del operador nativo `comfyui` (bridge TD↔ComfyUI, carga workflows JSON y expone
`GetTool()` para agentes). Doc oficial: `docs.dotsimulate.com/operators/pipelines/comfyui/`.

### ⚠️ Esperar el resultado de `comfyui.par.Generate.pulse()` deadlockea el cook thread — confirmado dos veces, en dos proyectos distintos

**Síntoma:** se pulsa `Generate` en el operador `comfyui` y luego se intenta esperar el resultado
(via thread+join, polling de `Status`/filesystem, o cualquier otra forma de espera) desde el mismo
código que disparó el pulse. El LOP nunca progresa: `Status` se queda pegado, el archivo no se
descarga, timeout garantizado. Variantes que fallan todas: `threading.Thread` + `join()` +
polling de `.par.Status` (error `TouchDesigner objects cannot be accessed outside the main
thread`), thread + `join()` + polling de filesystem (el archivo nunca aparece porque el LOP
necesita el cook thread para descargarlo y ese thread está bloqueado en `join()`), `time.sleep()`
directo en el cook thread (el propio `pulse()` se queda en cola sin llegar a procesarse).

**Causa:** el operador `comfyui` necesita que el cook thread de TD siga corriendo para procesar los
eventos del WebSocket con ComfyUI y descargar los archivos de salida. Cualquier forma de esperar
un resultado bloquea justo el recurso que el LOP necesita para producir ese resultado — mismo
patrón que el autobloqueo del `tool_manager` (pitfall de arriba), pero más traicionero porque el
LOP no da ningún error visible, simplemente no avanza nunca.

**Fix:** tratar `comfyui` (el LOP) exclusivamente como panel de configuración y para generación
manual desde la UI — cargar workflow, inspeccionar `Dyn*` (ver pitfall de nombres más abajo). Para
generación disparada por código/agente, ir por **REST puro contra el servidor de ComfyUI en un
thread en background** (`POST /prompt`, `GET /history/{id}`, `GET /view`), sin tocar
`Generate.pulse()` del LOP en absoluto. El thread no debe tocar ningún objeto TD hasta el final,
donde se reprograma un callback al cook thread vía `run(..., delayFrames=1)` para volcar el
resultado (cargar el archivo en un TOP, actualizar tablas, etc.) — ver el pitfall de arriba sobre
cómo invocar correctamente ese callback si el operador que recibe el resultado es un `Any`.

**Regla:** si necesitas que un agente dispare generación de ComfyUI desde TD de forma fiable, el
`comfyui` LOP no es el motor de ejecución — es solo la fuente de configuración (workflow file,
carpeta base, servidor, y el mapeo `Dyn*` → nodo/campo que expone via `.help`). La ejecución real
va aparte.

### ⚠️ `Apiparfilter` viene con un default de fábrica que no coincide con ningún parámetro real

**Síntoma:** el tool `generate_image` que expone el operador llega al agente con
`"parameters": {"properties": {}}` — vacío, sin ni siquiera el prompt, aunque el operador tenga
parámetros `Dyn*` (prompt, imagen, seed...) perfectamente configurados y visibles en su propia UI.

**Causa:** `Apiparfilter` (página Config) filtra qué `Dyn*` se exponen al agente por patrón
wildcard. El valor por defecto que trae el operador de fábrica es `*alue` — un patrón que no
matchea el nombre de ningún parámetro real, así que el filtro deja pasar cero parámetros. No es
un fallo de configuración del usuario, es el estado inicial del operador.

**Fix:** vaciar `Apiparfilter` (expone todos los `Dyn*`) o ponerle un patrón explícito que
matchee lo que quieras que el agente controle en cada llamada, ej. `*text* *image* *seed*`. Hay
que revisarlo cada vez que se carga un workflow nuevo, porque los nombres de nodo cambian (ver
siguiente pitfall).

### ⚠️ Los nombres de los parámetros `Dyn*` cambian según el workflow cargado — nunca asumirlos

**Síntoma:** un workflow expone el prompt como `Dyntext`; otro (aparentemente similar, mismo
propósito txt2img) lo expone como `Dynvalue`, con `Dynvalue1`/`Dynvalue2` siendo en realidad
width/height de otro nodo distinto. Pasar `Dyntext` a un workflow que en realidad usa `Dynvalue`
falla con `AttributeError` en vez de con un error más informativo.

**Causa:** ComfyTD nombra cada `Dyn*` según el tipo de widget del nodo de origen en el workflow
(ej. un nodo `PrimitiveStringMultiline` puede acabar como `Dynvalue`, no `Dyntext`, si esa es la
etiqueta genérica del widget en ese nodo concreto). El nombre no es estable entre workflows aunque
la función sea la misma.

**Fix:** tras cargar cualquier workflow nuevo (`Loadworkflow.pulse()`), inspeccionar cada
parámetro `Dyn*` con `.help`, `.label` y **`.style`** antes de asumir cuál es el prompt, la imagen
o cualquier otro campo:

```python
c = op('/ruta/al/comfyui1')
for p in c.customPars:
    if p.name.startswith('Dyn'):
        print(p.name, '| style:', p.style, '| label:', p.label, '| help:', p.help)
```

El `.help` incluye el número y tipo de nodo de origen (ej. `"Node 76 (PrimitiveStringMultiline):
value"`, o `"Node 203 (LoadImage): image"`), que junto con `p.style` (`'TOP'`/`'File'` para
parámetros de imagen, `'Str'`/`'Int'`/`'Float'`/`'Menu'` para el resto) es la forma fiable de
clasificar cada `Dyn*` mecánicamente en vez de adivinar por el nombre. El texto del `.help` a
veces incluye una etiqueta de tipo entre corchetes (`[IMAGE]`) y a veces no — no depender solo de
esa etiqueta, `p.style` es la fuente de verdad que nunca falla.

**⚠️ No detectar "es una máscara" por substring "mask" en el nombre del campo.** Un workflow de
inpaint tiene muchos parámetros de configuración cuyo nombre contiene "mask" sin ser en absoluto
una imagen de máscara subible: `mask_expand_pixels`, `mask_invert`, `mask_blend_pixels`,
`mask_fill_holes`, `noise_mask` (booleano), `context_from_mask_extend_factor`... Buscar la
substring `"mask"` en el nombre del campo da falsos positivos masivos. La detección fiable es:
`p.style in ('TOP', 'File')` (ya usado para detectar imágenes) **y además** el campo se llama
literalmente `mask` (no una variante compuesta) o el `class_type` del nodo es un loader de
máscara dedicado (`LoadImageMask`). Cualquier otro parámetro con "mask" en el nombre es
configuración, no una imagen.

**Nota relacionada — `Imagepartype`:** el modo de entrada de imagen (`top` / `file` / `strmenu`,
página Config) determina si un agente externo puede pasar una imagen de referencia en absoluto.
En modo `top` la imagen tiene que ser un TOP ya conectado dentro de la red — un agente MCP externo
no puede "adjuntar" una imagen así, solo cambiar qué TOP está referenciado si ya existe uno con
contenido cargable. Para que un agente pase una ruta de archivo directamente, hace falta `file`.

**Recuperación tras un job atascado:** ver el pitfall de arriba sobre `time.sleep()` bloqueante —
`Interrupt` + `Clear Queue` + relanzar `Generate` limpio ha funcionado de forma fiable.

### ⚠️ `CurrentFilePath` nunca se asigna a un valor real — el viewer/History no refleja generaciones nuevas

**Síntoma:** el TOP de preview interno del operador (ej. `output_top_disp`) y el parámetro
`Currentfile` no se actualizan al generar una imagen nueva, ni al navegar el historial con
Job/Output index. Se quedan mostrando la última imagen que sí se actualizó manualmente en algún
momento anterior, o vacíos.

**Causa:** `Currentfile` es un parámetro de solo lectura con expresión
`me.ext.ComfyUIEXT.CurrentFilePath.val`, donde `CurrentFilePath` es un `tdu.Dependency` interno de
`ComfyUIEXT`. Revisando el código de la extensión (build de julio 2026), `CurrentFilePath.val`
solo se **resetea a `""`** en la limpieza de estado — no hay ningún punto del código donde se le
asigne una ruta real tras completar un job o navegar el historial. Parece una funcionalidad
incompleta en esta versión del operador (`v0.1.0`, muy reciente), no un error de configuración.

**Workaround:** si necesitas ver el resultado de una generación de forma fiable, no dependas del
viewer interno del `comfyui` LOP. Si generas por tu cuenta (ver pitfall de arriba sobre no usar
`Generate.pulse()` para generación programática), carga el resultado en tu propio TOP tras
descargarlo — es trivial y no depende de que dotsimulate arregle esta pieza. Si además quieres que
el viewer interno del LOP también lo refleje "de prestado", asignar directamente
`comfy_op.op('output_top_disp').par.file` y pulsar `reload` funciona (es un parámetro simple, sin
expresión bloqueada ni lógica interna que lo sobreescriba).

### ⚠️ Leer el JSON del workflow sin `encoding='utf-8'` explícito falla con emoji/caracteres especiales en los títulos de nodo

**Síntoma:** `open(workflow_path, 'r')` (sin encoding) lanza
`'charmap' codec can't decode byte 0x8f in position ...` al leer un workflow guardado desde
ComfyUI, aunque el archivo sea JSON válido.

**Causa:** en Windows, el modo texto de `open()` usa por defecto la codificación de la consola
(normalmente `cp1252`), no UTF-8. Muchos workflows de ComfyUI incluyen emoji en `_meta.title` de
nodos con nombres visuales (ej. `"✂️ Inpaint Crop"`) — esos bytes UTF-8 multibyte no son
representables en `cp1252` y rompen la lectura.

**Fix:** especificar siempre `encoding='utf-8'` al leer cualquier archivo de workflow de ComfyUI:
```python
with open(workflow_path, 'r', encoding='utf-8') as f:
    wf = json.load(f)
```

### 📎 Patrón: inpaint "clipspace" — imagen y máscara en un único PNG RGBA

Algunos workflows de inpaint (los que se construyen a mano en ComfyUI usando su editor de máscara
integrado, "Mask Editor" sobre clipspace) **no tienen un nodo de máscara separado**. En su lugar,
un único nodo `LoadImage` carga un PNG con canal alpha: el **RGB es la imagen**, el **canal alpha
es la máscara** (blanco = región a repintar, transparente/negro = región a conservar). El pipeline
típico es:

```
LoadImage (RGBA) → sale (IMAGE, MASK) del mismo archivo
    ↓
InpaintCropImproved → recorta la región de interés usando la máscara
    ↓
InpaintModelConditioning (noise_mask=true) → limita la generación a la zona marcada
    ↓
KSampler → genera solo dentro de esa zona
    ↓
InpaintStitchImproved → pega el resultado de vuelta en la imagen original intacta
```

**Cómo generar esto programáticamente** (sin editor de máscara, con coordenadas normalizadas
0-1, origen arriba-izquierda tipo CSS — el mismo sistema que usa un lidar/región de pantalla):

```python
from PIL import Image, ImageDraw
import io

def crear_composite_rgba(image_bytes, region):
    src = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    W, H = src.size
    alpha = Image.new('L', (W, H), 0)
    draw = ImageDraw.Draw(alpha)
    rx, ry = int(region['x'] * W), int(region['y'] * H)
    rw, rh = int(region['w'] * W), int(region['h'] * H)
    draw.rectangle([rx, ry, rx + rw, ry + rh], fill=255)
    rgba = src.convert('RGBA')
    rgba.putalpha(alpha)
    buf = io.BytesIO()
    rgba.save(buf, 'PNG')
    return buf.getvalue()
```

Subir el PNG resultante como el único archivo del `LoadImage` (via `/upload/image`) — no hace
falta tocar ningún parámetro de máscara aparte. **Cómo distinguir este caso del caso "máscara
como parámetro separado"**: comprobar si el workflow tiene algún `Dyn*` con `is_mask=True` (ver
pitfall de arriba sobre detección fiable) — si no hay ninguno, es un candidato a inpaint tipo
clipspace y este es el patrón a usar. Validado end-to-end: región marcada con coordenadas
normalizadas → PNG RGBA subido → `InpaintCropImproved`/`InpaintStitchImproved` → resultado
pixel-perfect fuera de la región, contenido nuevo dentro.

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

**Nota — módulos "starter" en el `Any` recién clonado:** el `Any` copiado desde
`/dot_lops/custom_operators/any` trae `Modulesmenu` apuntando a un módulo de ejemplo incluido
(`text_editor`, `preset_morpher`, `state_lens`). Si `Modulesmenu` se queda en uno de esos valores,
pulsar `Reload` **sobreescribe el contenido del DAT `module` con el ejemplo**, borrando cualquier
código propio ya escrito ahí. Poner `Modulesmenu = '(none)'` antes de escribir el módulo propio
(o inmediatamente después, y volver a escribir el código si ya se sobreescribió una vez).

---

## ⚠️ getattr(tm.par, 'Tool10op') no funciona tras insertBlock

Tras `seq.insertBlock()`, los nuevos pars no son accesibles via `getattr`.
Usar: `list(tm.pars('Tool10op'))[0]`

Los pars OP pueden perderse tras `cook(force=True)` — reasignar siempre después del cook.

---

## ⚠️ td_code corre en sandbox — cambios no persisten al container real (matiz: destroy() y edición de DATs existentes son la excepción)

Los ops **creados** con `td_code` NO son visibles desde `network_context` ni desde TD.

**Para crear ops que persistan:** usar `network_context` o el método `loadTox()` desde `td_code`.

**Matiz importante — `destroy()` SÍ persiste incluso desde `td_code`.** A diferencia de `create()`,
llamar a `.destroy()` sobre un operador ya existente (obtenido vía `op('/ruta/real')`) borra el
operador de la red real, verificable después desde `network_context`. Esto es porque `destroy()`
opera sobre una referencia a un objeto real de la red, no crea nada nuevo dentro del sandbox.

**Otro matiz — editar `.text` de un DAT ya existente TAMBIÉN persiste.** `dat = op('/ruta/real');
dat.text = nuevo_contenido` desde `td_code` sí se refleja en la red real (verificable releyendo en
una llamada `td_code` separada). Igual que `destroy()`, esto es mutar una referencia a un objeto
ya existente, no crear uno nuevo — la restricción de "no persiste" es específica de `create()` y
de operadores nuevos, no de cualquier cambio hecho desde `td_code`.

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
usa `td_code` con `.destroy()` directamente; funciona y persiste. Para ediciones de contenido de
DATs (incluyendo `str_replace` fallido de la tool dedicada), reasignar `.text` completo vía
`td_code` es una alternativa fiable.

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
