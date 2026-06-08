
raw
Comunicación Claude ↔ TouchDesigner via LOPs
 
Guía de onboarding para cualquier instancia de Claude que tenga que operar en un proyecto TouchDesigner que use el LOPs pack (dotsimulate).
 
Audiencia: Claude (cualquier modelo/versión). Asume que tienes acceso al MCP touchdesigner-lop (o equivalente) y a tu propio set de tools internas (view, create_file, bash_tool, etc.).
Origen: experiencia acumulada en el proyecto GIVAH Immersive entre mayo y junio 2026, contrastada con la documentación oficial dotsimulate.
Última revisión: 6 de junio de 2026.
 
1 · Por qué existe este documento
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
 
 
2 · Qué es LOPs
LOPs (Language Operator Pack) es un add-on de dotsimulate para TouchDesigner que añade una familia de operadores especializados en construir aplicaciones con LLMs dentro de TD. No es Python suelto — son operadores TD nativos con sus parámetros, conexiones, callbacks, etc.
Cada operador LOP:
 
Tiene la tag LOP y otra específica del tipo (agentLOP, tool_managerLOP, etc.)
Vive típicamente en /project1/<nombre>1 (como cualquier baseCOMP TD)
Tiene una página custom con sus parámetros (sin tocar la página Common/Layout/Look)
Suele tener un sub-COMP Logger y un sub-DAT logs para diagnóstico
Muchos exponen un método GetTool() que devuelve schemas de herramienta para conectarlos a un Agent LOP o a un MCP server
 
Lo que LOPs resuelve: integrar agentes LLM en pipelines audiovisuales sin escribir un servidor por separado. El agente vive en el mismo grafo que el render, los inputs de mic, los outputs de pantalla.
 
3 · Setup: cómo conectar y verificar acceso
3.1 El MCP touchdesigner-lop
El usuario te conecta a su proyecto a través de un servidor MCP. Las tools principales que verás son (nombres pueden variar según versión):
ToolPara quéget_project_infoFPS, resolución, nombre del proyecto. Smoke test iniciallist_operatorsListar hijos de un COMP (por defecto /project1)get_operator_infoParámetros, conexiones, errores de un operadorset_parameterCambiar UN parámetro (value como string)execute_pythonTu herramienta principal. Ejecuta Python arbitrario en el contexto de TDread_dat / write_datLeer/escribir contenido de un DATget_chop_channelsCanales y valores de un CHOP
Si tienes el MCP de Anthropic más reciente (touchdesigner:) también tienes execute_python_script con modos read-only/safe-write/full-exec y get_exec_log para auditar lo que has hecho. Si tienes ambos sets, el de Anthropic suele dar más feedback estructurado; el touchdesigner-lop:execute_python es más directo.
3.2 Verificación al arrancar (primera operación SIEMPRE)
python# Smoke test: ¿estamos conectados?
print(f"FPS: {project.cookRate}")
print(f"Operadores en /project1: {len(op('/project1').children)}")
 
# Inventario LOPs del proyecto
lops = [c.path for c in op('/project1').children if hasattr(c,'tags') and 'LOP' in c.tags]
print(f"LOPs encontrados: {len(lops)}")
for p in lops: print(f"  {p}")
Si esto funciona, estás dentro. Si falla, dile al usuario: "no tengo conexión con TD, ¿puedes verificar que el servidor MCP está activo?".
 
4 · Catálogo de operadores LOPs
Lo que sigue es una guía operativa, no exhaustiva. Para cualquier operador, inspecciona sus parámetros antes de tocarlos (get_operator_info o iterando op.pars()).
4.1 Agent LOP — el cerebro
Tags: LOP, agentLOP. Tipo: container.
El operador central. Es un wrapper sobre una llamada a un LLM (Anthropic, OpenAI, Ollama, etc.) con:
 
System prompt (DAT)
Context grabber opcional (DATs inyectados como system message en cada turno)
Lista de tools (otros LOPs conectados a su Tool sequence)
Conversación persistida (_api_messages interno, sesión nombrada o efímera)
Callbacks para integración con el resto del grafo
 
Parámetros clave:
 
Apiserver: anthropic / openai / ollama / etc.
Model: string menu (los más comunes en Anthropic: claude-sonnet-4-6, claude-haiku-4-5-20251001, claude-opus-4-6)
Systemmessagedat: DAT con el system prompt. El agente lee de <agent>/system_prompt, NO directamente del DAT que apuntas — hay copia interna al inicializar
Contextop: COMP con DATs inyectados en cada turno como system message (útil para info que cambia)
Sessionmode: named (persiste) o efimera
Sessionid: nombre de la sesión actual
Maxresultchars: tope de chars que una tool puede devolverle al agente. Default 16K, clampMax 100K — ¡insuficiente para tablas grandes! Si tu Tool devuelve >100K chars truncará silenciosamente. Quitar el clampMax y poner 250000 si lo necesitas
Toolturnbudget: máximo de tool-call rounds por query
Costbudget: tope en USD por query (corta si lo supera)
Paralleltoolcalls: si True, el agente puede llamar varias tools en un solo turn
 
Tool sequence: agent.seq.Tool.numBlocks = N define cuántos slots tiene. Cada slot tiene Tool<i>toolop (operador) y Tool<i>toolactive (on/off).
Forzar re-parse de tools (importante):
pythonagent.par.reinitextensions.pulse()
Tras esto, el log debe decir Parsed N tools from M blocks.
Limpiar sesión:
pythonagent.par.Clearsession.pulse()
Pitfall: Active flickea a False entre tool calls batched. NO uses Active como única señal de "el agente terminó". Usa combinación de Agentstatus, Active y turn_table.numRows.
4.2 ChatTD — el motor compartido
Path típico: /dot_lops/ChatTD. Tipo: base.
Background runtime que muchos LOPs necesitan (especialmente Tool Manager, MCP servers, operadores con SideCar). Si está mal configurado, los LOPs que dependen de él reportan Status: Missing dependencies o no arrancan.
Tiene un parámetro crítico: Python Venv — apunta al venv donde se instalan dependencias para SideCars. Detalle clave en §5.4.
4.3 Tool DAT (tool_datLOP)
Tags: LOP, tool_datLOP.
Expone operaciones sobre un Table DAT (o Text DAT) como tool para el agente. Versión actual: v2.4.0 (las anteriores tenían bugs serios — ver §5.2).
Parámetros clave:
 
Target: DAT que la herramienta puede leer/escribir
Preset: read_only / append_only / custom
Toolname: prefijo que se aplica a las sub-operaciones. CRÍTICO: cada Tool DAT del Agent debe tener un Toolname distinto, si no, las sub-operaciones (read_content, append_row, etc.) colisionan
Responseverbosity: minimal / diff / full. Para tools de lectura usa full; para escritura, minimal
Maxrows: tope de filas que la tabla puede tener
 
Una Tool DAT puede exponer varias sub-operaciones al agente (read_content, append_row, replace_all_table, insert_row, delete_row, etc.). El nombre que ve el agente es <Toolname>_<operacion> (ej. buscar_catalogo_read_content).
Pitfall histórico (resuelto en v2.4.0): dos Tool DATs con default Toolname='edit_td_dat' colisionaban → DUPLICATE TOOL 'append_row' — ALL TOOLS DISABLED. Ahora siempre poner Toolname único.
4.4 Tool Request LOP (tool_requestLOP)
Tool que hace una llamada HTTP externa. Útil para servicios de generación de imagen, voz, etc. Cada uno expone 1 tool con su schema.
Configuración típica: URL del endpoint, headers, parser de respuesta, mapeo de outputs a DATs del proyecto.
4.5 Tool Parameter LOP (tool_parameterLOP)
Expone parámetros de un operador como tool. El agente puede leerlos/escribirlos directamente. Útil para que el agente controle un nodo concreto (volume, color, posición) sin escribir código.
4.6 Tool TD Mod (tool_td_modLOP) ⭐ recomendado
El patrón nuevo (junio 2026) que recomendamos sobre Tool DAT cuando hay validación compleja.
Expone módulos Python como tools. El agente recibe una sola tool (td_mod) con 4 actions: list, doc, source, call.
Parámetros clave:
 
Toolprefix + Toolname: nombre final = td_mod por defecto
Modulescomp: COMP donde viven los module DATs (típicamente <self>/modules)
Stripmodprefix: si vale td_, un DAT llamado td_givah se expone como módulo givah
 
Para añadir tu propio módulo:
 
Crear un Text DAT en el Modulescomp con nombre td_<algo>
Escribir Python normal con funciones documentadas y typed:
 
pythondef mi_funcion(arg1: str, arg2: int = 0) -> dict:
    """Descripción que el agente lee.
    
    Args:
        arg1: descripción
        arg2: descripción
    
    Returns:
        descripción
    """
    if arg1 not in ("opcion_a", "opcion_b"):
        return {"ok": False, "error": f"arg1 invalido: {arg1}. Usa opcion_a|opcion_b"}
    # ... lógica ...
    return {"ok": True}
 
Verificar exposición: tool_td_mod1.GetTool() debe incluir la signature en args.description
 
Por qué es mejor que Tool DAT para validación compleja:
 
Errores semánticos en español/inglés natural (no Row index 2 out of bounds)
Validación de args al inicio de la función → el agente recibe el error antes de tocar nada
El agente lee la firma + docstring antes de llamar (con action="doc")
Un solo slot en el Agent reemplaza N Tool DATs
El agente se autocorrige leyendo el mensaje de error sin intervención humana
 
Acción list: catálogo compacto de módulos disponibles
Acción doc: docstrings + signatures de un módulo o función concreta
Acción source: Python source raw
Acción call: invoca <modulo>.<funcion>(**kwargs) con args validados
Módulos starter incluidos: catalog (op type discovery), net (network manipulation), search (descubrir otros módulos).
4.7 Tool TD Code (tool_td_codeLOP)
Tool que ejecuta Python arbitrario en el contexto TD. Tiene safety blocking + path restrictions configurables. Más permisivo y peligroso que Tool TD Mod.
Cuándo usarlo: si necesitas que el agente haga inspección amplia del proyecto o tareas que no caben bien en módulos predefinidos. Reservar para agentes de desarrollo, no para agentes de producción.
4.8 Tool VFS (tool_vfsLOP)
Sistema de archivos virtual sandboxed en memoria, persistente en el .toe. 7 tools al agente: read/write/list/search/delete/copy/move.
Setup:
 
Crear el operador
Pulsar Checkvfs con Createifmissing=True → crea automáticamente <self>_virtualFile baseCOMP
 
Caso de uso típico: memoria de trabajo del agente separada del log oficial. Notas de razonamiento, hipótesis, borradores que el agente puede revisar en turnos siguientes sin contaminar la conversación principal.
Limitaciones: solo text/JSON (no binarios), tope de 5MB por archivo, claves bajo 200 chars sin whitespace/slashes/quotes.
4.9 Tool Manager (tool_managerLOP) ⭐ útil para refactor
Dos roles a la vez:
 
Agregador: su GetTool() devuelve TODOS los tools enabled en su sequence. Conectado a un Agent, un solo slot en el Agent expone N tools
MCP server: hostea esos mismos tools via stdio o streamable-http para clientes externos (Claude Desktop, Cursor, etc.)
 
Requisitos: ChatTD configurado + dependencies fastmcp + td_mcp_adapter instaladas en el venv del ChatTD.
Workflow correcto para añadir tools:
 
Añadir slot en Tool sequence apuntando al operador
Refreshtools.pulse() → relee schemas
Restartserver.pulse() → sin esto el server no usa los nuevos tools
 
Sistema de presets: guarda configuraciones de toggles individuales (Tool Toggle page) y conmuta entre ellas en runtime. Útil para "modos" del agente sin tocar el system_message.
Pitfall: el parámetro Running antes laguabaa respecto a la realidad. Confiar en op('<manager>/server_state').text (JSON con running, port, host, timestamp) como fuente de verdad.
4.10 Tool Registry (tool_registryLOP)
Utility para descubrir y asignar tools a agents desde una sola UI.
Workflow:
 
Searchscope (Current Level / Parent Level / Entire Project) + Maxdepth
Scannetwork.pulse() → puebla los menús Selectedtool y Targetagent
Seleccionar tool + agent
Assigntool.pulse() → añade el tool al Tool sequence del agent
 
Detecta tools (ops con GetTool() y tag LOP) y agents (ops con Tool sequence y tag LOP). Excluye /ui/ y /sys/.
Pitfall: el parámetro Status solo se actualiza tras Assign, no tras Scan. No lo uses como confirmación de scan; mira los menús.
4.11 Tool Monitor (tool_monitorLOP)
Tracking de actividad del USUARIO en TD: qué operador seleccionas, qué parámetros tocas, qué errores aparecen.
Diseñado para: agente que AYUDA al humano operando TD (asistente de desarrollo, copiloto).
NO útil para: humano observando lo que hace un agente (testing de agentes en producción). Para eso, usa agent.op('turn_table') y agent.op('conversation_dat').
Tools que expone: get_recent_activity (lista de eventos recientes con timestamps y diffs), capture_network_screenshot (PNG base64 del editor TD; requiere modelo con visión).
4.12 Tool Op Context (tool_op_contextLOP)
Análisis profundo de un operador concreto: parámetros, conexiones, performance, contenido de DATs, errores.
1 tool con 5 análisis: quick_summary, troubleshoot, optimize, explain, get_content.
Útil para: asistentes de desarrollo TD que ayudan a entender qué hace un operador o por qué falla.
NO útil para: agentes de aplicación (como GIVAH, que facilita sesiones de hospitality — no edita TD).
4.13 Claude Code (claude_codeLOP) ⚠ uso reservado
Bridge a la CLI local de Claude Code via WebSocket. Auto-lanza el bridge server, persiste sesiones, expone tools de Claude Code (Bash, Read, Write, etc.) y opcionalmente tools TD del proyecto.
Coste: consume el cap de suscripción Pro/Max del usuario. Bridge log típico: Cost: $0.015505 (subscription). NO es gratis aunque no se cobre por token API.
Cuándo usar:
 
Tareas one-shot complejas de scaffolding o refactor
Generación de código que requiere browsing del filesystem y ejecución de comandos
Crear tools nuevas complejas (ej. selección de coordenadas con lidar, scripts de migración)
 
Cuándo NO usar:
 
Como agente principal en producción (caro y desperdicia cap)
Para evaluación rutinaria de otros agentes (caro)
Para tareas que el MCP normal de TD ya cubre
 
Pitfalls específicos:
 
Permissionmode='bypassPermissions' necesario para automatización (default pausa esperando aprobación humana)
Sendinterrupt + Sendquery inmediato puede matar el bridge. Para reanimar: Launchbridge.pulse() (NO Connect.pulse())
Prompts largos con reasoning extenso pueden colgarse silenciosamente. Vigila el bridge_log
 
Workflow recomendado:
pythoncc = op('/project1/claude_code1')
cc.par.Permissionmode = 'bypassPermissions'  # solo para automatización supervisada
cc.par.Workingdir = '/ruta/al/repo'           # NO el .toe folder, un repo aparte
cc.par.Prompt = 'descripción concreta de la tarea one-shot'
cc.par.Sendquery.pulse()
# Esperar viendo cc.par.Currentsession y cc.op('output_dat')
4.14 Agent Swarm (agent_swarmLOP)
Coordinación lead+workers entre múltiples Agent LOPs. Un agent lead delega a workers, recoge resultados, decide próximo paso.
Protocolos: background_parallel, foreground_deferred, audit_recovery, strict_pipeline.
Caso de uso típico: un lead estratégico (Sonnet) coordinando workers especializados (varios Haiku) para tareas paralelizables.
No usar para: agentes de conversación 1-a-1 con usuario (sobre-ingeniería). Útil cuando un problema se beneficia de descomposición en sub-tareas.
4.15 Any (anyLOP)
Operador genérico que carga un módulo Python externo y expone sus funciones como tools. Más simple que tool_td_mod para casos puntuales: un solo módulo, sin sistema de catálogo.
Workflow: Scan Modules → Modulesmenu → Loadfromlibrary. Tres starter modules incluidos: text_editor, state_lens (escanear estado de la red), preset_morpher.
4.16 Context Grabber (context_grabberLOP)
Agrupa varios DATs en un solo "context" que el Agent LOP inyecta como system message en cada turno. Útil para info que cambia entre turnos (estado actual, tablas vivas, valores de CHOPs serializados).
Slot 0..N apunta a DATs. El Agent los lee en cada call y los prepende al system prompt.
Pitfall: si el contexto crece mucho, gastas tokens en cada turno. Limita slots a info realmente dinámica; lo estable va en el system message base.
4.17 Chat Viewer (chat_viewerLOP)
Panel UI para visualizar el conversation_dat o turn_table de un Agent durante desarrollo. No es funcionalmente necesario, pero ayuda muchísimo a debug.
 
5 · Patrones de trabajo
5.1 Inspeccionar un proyecto desconocido
python# Inventario rápido
print(f"=== Proyecto: {project.name} ===")
print(f"FPS: {project.cookRate}, Resolución: {project.resolution}")
 
# Hijos de /project1 clasificados
proj = op('/project1')
lops = [c for c in proj.children if 'LOP' in c.tags]
tools = [c for c in proj.children if any(t in c.tags for t in ('tool_datLOP','tool_requestLOP','tool_parameterLOP'))]
agents = [c for c in proj.children if 'agentLOP' in c.tags]
 
print(f"LOPs: {len(lops)}, Tools: {len(tools)}, Agents: {len(agents)}")
for a in agents:
    print(f"  Agent {a.name}: modelo={a.par.Model.eval()}, tools={a.par.Tool.sequence.numBlocks}")
5.2 Crear un agente de pruebas sin tocar producción
Si necesitas probar una tool nueva o un patrón nuevo sin gastar dinero ni romper el agente en producción:
python# Copia el agente existente como base
src = op('/project1/agent_REAL')
proj = op('/project1')
if proj.op('agent_test'): proj.op('agent_test').destroy()
ag = proj.copy(src, name='agent_test')
 
# Configuración barata
ag.par.Model = 'claude-haiku-4-5-20251001'   # el más barato
ag.par.Maxtokens = 1024                       # contención
ag.par.Toolturnbudget = 3
ag.par.Costbudget = 0.10                      # corte duro $0.10
ag.par.Sessionid = 'test_001'                  # sesión independiente
ag.par.Contextop = None                        # sin context_grabber heredado
ag.par.Prompt = ''
ag.par.Useannotate = False
ag.par.Active = False
ag.par.Clearsession.pulse()
 
# Vaciar tools y poner solo lo que quieres probar
ag.par.Tool.sequence.numBlocks = 1
ag.par.Tool0toolop = '/project1/tool_a_probar'
ag.par.Tool0toolactive = 'on'
 
# System prompt mínimo
ag.op('system_prompt').text = 'Eres un agente de prueba. Sé breve.'
 
# Forzar re-parse
ag.par.reinitextensions.pulse()
5.3 Lanzar un turno y observar resultado
pythonag = op('/project1/agent_test')
ag.par.Prompt = 'Tu prompt aquí'
ag.par.Call.pulse()
# El agente cookea. NO uses time.sleep() — bloquea el cook thread.
# En su lugar, vuelve a consultar en una segunda invocación del MCP.
En la segunda invocación:
pythonag = op('/project1/agent_test')
print(f"Status: {ag.par.Agentstatus.eval()}")
print(f"Active: {ag.par.Active.eval()}")
 
# Respuesta final del agente
print(f"output_dat: {ag.op('output_dat').text}")
 
# Ciclo de turnos (tool_calls, tool_results, responses)
turn = ag.op('turn_table')
for r in range(1, turn.numRows):
    row = [str(turn[r,c].val)[:80] for c in range(turn.numCols)]
    print(f"  [{r}] {row}")
5.4 Instalar dependencias para LOPs correctamente
Pitfall histórico: los LOPs con SideCar (Tool Manager, Voice Activity, STT, etc.) corren en un proceso aparte que usa el venv apuntado por ChatTD.par.Python Venv. Si haces pip install en otro Python (incluso el bundled de TD), el SideCar no lo verá.
La forma correcta:
 
Abrir el operador Python Manager (suele estar cerca de ChatTD)
Pulsar "Open Console" → terminal con el venv ya activo
pip install <paquete> (sin rutas)
 
Si pip da [WinError 5] Acceso denegado:
 
Cerrar TD completamente
taskkill /F /IM python.exe (workers zombies bloquean .pyd files)
Reabrir TD → Python Manager → Open Console → pip install
Si nada funciona, reboot
 
 
6 · Pitfalls universales aprendidos (todas las lecciones de proyectos previos)
6.1 Threading y cook
 
time.sleep() >1s dentro de execute_python BLOQUEA el cook thread de TD. Consecuencias: bridges desconectan, tool_use queda stuck, tu MCP da timeout a los 4 minutos. Para polling: hacer queries cortas y separadas en múltiples invocaciones del MCP.
TD no es multithread en cooking. Si lanzas algo costoso, hazlo asincrónico o aceptas frames perdidos.
 
6.2 Agent LOP
 
Active flickea a False entre tool_calls batcheados. Usa combinación con Agentstatus y turn_table.numRows.
El conversation_dat puede aparecer vacío visualmente (filas vacías en preview). La verdad está en _api_messages interno O en turn_table (más legible).
Clearsession.pulse() mientras hay una call en flight deja estado "orphaned callback" que persiste 20-30s. Fix: reinitextensions.pulse().
Tras cambios en seq.Tool o en system_message: SIEMPRE reinitextensions.pulse(). Log debe decir Parsed N tools from M blocks.
Maxresultchars default 16K, clampMax 100K. Trunca silenciosamente. Desactivar clampMax y poner 250000 para tablas grandes.
Para añadir slot Python: ag.par.Tool.sequence.numBlocks = N (no ag.par.Tool.val = N).
El agente lee de <agent>/system_prompt, no del DAT que apuntas en Systemmessagedat. Si actualizas el template, propagar a ambos.
 
6.3 Tool DAT v2.4.0
 
Cada Tool DAT en el mismo agente debe tener Toolname DISTINTO. Default edit_td_dat causa colisiones. Síntoma fatal: DUPLICATE TOOL 'append_row' — ALL TOOLS DISABLED.
Responseverbosity: minimal solo dice success/fail. Inútil para lecturas. Para read tools usa full.
view_range solo aplica a Text DAT, no a Table DAT. Tablas devuelven todo de golpe (cuidado con tamaño).
replace_all_table con content=[[a,b],...] reescribe el header con la primera fila. Detectar con if str(tbl[0,0]).lower() in ['nombre','name',...]: start_row=1.
Bug histórico: insert_row(row=N) con N > Maxrows da error críptico. Pasar a tool_td_mod con función Python typed lo resuelve.
 
6.4 Tool Manager
 
Después de añadir slots: Refreshtools.pulse() SOLO. Para que el server hosted use los nuevos: Restartserver.pulse() también.
Running par lagueaba en versiones antiguas; consultar server_state JSON como verdad.
Save preset 2 veces seguidas muy rápido puede sobrescribir el primero. Cambiar Presetname antes de cada Savepreset.pulse().
 
6.5 Tool VFS
 
Checkvfs.pulse() con Createifmissing=True crea automáticamente el VirtualFile component. Sin esto, el Agent reporta "no tools".
 
6.6 Operadores TD genéricos
 
baseCOMP no permite interacción de panel; necesita containerCOMP. Algunos LOPs pegan un container interactive dentro de un base no-interactive — si necesitas eventos, extrae con parent.copy().
DAT Execute con re-entrancia: usar flag me.storage["processing"] = True para evitar loops.
webserverDAT.par.transparent (toggle minúscula).
parameterexecuteDAT.par.pars (no parameters).
Float custom pars con clampMin/clampMax: setear .min y .max explícitamente.
textDATs usados como callbacks NECESITAN language=python explícito (default text, silent skip).
 
6.7 webserverDAT headers
Setear como atributos individuales en el dict response, NO como sub-dict:
pythonresponse["Access-Control-Allow-Origin"] = "*"  # ✓
# response["headers"] = {"...": "..."}          # ✗
6.8 Strings con regex
Backslashes en triple-quoted strings que vas a usar como regex se sobre-escapan. Usar raw strings o escapar a mano.
6.9 Numpy/torch ABI
Subir numpy o torch puede romper el ABI con otras libs (Resemblyzer, Silero VAD, EfficientWord-Net). Si algo falla tras un upgrade, actualizar torch/torchaudio también en la misma consola del Python Manager.
6.10 Callbacks de datexecuteDAT (y otros executes) NO disparan cuando modificas desde el MCP ⚠️
Esta es una de las trampas más confusas del MCP. Léelo con atención antes de construir cualquier watcher.
Cuando una instancia de Claude opera el proyecto vía MCP (touchdesigner-lop:execute_python) y hace mutaciones como:
pythonop('/project1/mi_tabla').appendRow([...])
op('/project1/mi_tabla').cells[r,c] = 'nuevo valor'
…la tabla se modifica correctamente (numRows aumenta, las celdas tienen el nuevo valor), pero los datexecuteDAT que la vigilan NO reciben los callbacks onTableChange / onSizeChange / onRowChange. La mutación es real pero TD no la marca como propagable a sus dependientes.
En cambio, las mismas mutaciones hechas desde el runtime interno de TD (callback del bridge de un LOP, sub-thread de un operador, dat.run() de un textDAT ejecutado en cook, parexec, evento de timer COMP…) sí disparan los callbacks con normalidad.
Es la misma familia que el bug "tablechange desde SideCar puede no propagarse" (originalmente identificado con mostrar_galeria en GIVAH), pero también afecta al MCP externo.
Síntoma típico: construyes un watcher, lo testeas vía MCP modificando la tabla a mano, los callbacks no disparan, asumes que tu código está mal y empiezas a reescribirlo. No lo está. El watcher funciona perfecto en producción, lo que está roto es tu método de test.
Cómo testear un watcher correctamente cuando sospechas del callback:
 
Llamar la función de callback directamente sin esperar al evento:
 
python   mod = op('/project1/tool_td_mod1/modules/td_givah').module
   mod._on_blast_complete(row_idx, log_dat)  # invocación directa
Esto verifica la lógica del callback aislada del mecanismo de eventos.
 
Disparar el evento desde dentro de TD, no desde el MCP. Por ejemplo, pulsar un parámetro real del operador que normalmente genera la mutación, o lanzar una operación pequeña del propio LOP que vigila el watcher. Si esa operación dispara propagation real, el watcher reacciona.
Como último recurso, mirar dat.totalCooks antes y después. Si no incrementa tras tu appendRow, sabes que TD no está propagando — el problema es el método, no el código.
 
Lo mismo aplica a parameterexecuteDAT cuando cambias un parámetro desde el MCP: a veces sí propaga, a veces no, dependiendo del operador. No confíes en que par.<X> = valor desde MCP dispare un parexec hasta haberlo verificado en el proyecto concreto.
6.11 me.storage es el lugar correcto para estado persistente en DAT executes
Si un DAT execute necesita mantener estado entre invocaciones de sus callbacks (contador de filas vistas, último ID procesado, flag de re-entrancia, cache, etc.), NO uses variables de módulo a nivel raíz del código del DAT:
python# MAL: se resetea en cada recompilación del DAT (incluso al cambiar par.dat)
_PREV_ROWS = {}
 
def onTableChange(dat):
    _PREV_ROWS[dat.path] = dat.numRows
Usa me.storage, que persiste entre recompilaciones del código y con el .toe:
python# BIEN
def onTableChange(dat):
    key = "prev_rows__" + dat.path
    prev = me.fetch(key, None)
    cur = dat.numRows
    if prev is not None and cur > prev:
        # ... procesar filas nuevas ...
    me.store(key, cur)
Ventajas:
 
Persiste entre recompilaciones del código del DAT.
Persiste con el .toe cuando se guarda el proyecto.
Inspeccionable desde fuera: op('.../watcher').storage
Reseteable: op('.../watcher').unstore('*')
 
Esto generaliza el patrón ya mencionado en 6.6 para re-entrancia. Si un DAT execute "olvida" lo que sabía entre disparos, casi siempre es porque el estado vivía en variables de módulo que se perdieron.
 
7 · Cuándo usar Claude Code
Tarea¿Claude Code?Agente principal de la aplicación en producción❌ NO. Caro por suscripción. Usa Agent LOP + API Anthropic directoEvaluación rutinaria de un agente❌ NO. Usa tu propio MCP a TD (este Claude que está leyendo)Crear un Tool nuevo simple❌ NO. Hazlo tú via execute_pythonRefactor grande de una sub-red TD✅ Sí, una sesión one-shotScript de migración de datos / scaffold de N operadores✅ SíTool compleja que requiere browsing del filesystem + bash✅ Sí (lidar coordinate selection, generación de assets, etc.)Generación de código que el usuario va a revisar antes de usar✅ Sí
Antes de invocar Claude Code, pregunta:
 
¿La tarea cabe en una sesión one-shot (≤30 min) o necesita supervisión continua?
¿El usuario está OK con consumir su cap de suscripción?
¿Puedes hacerla tú directamente con execute_python en menos tiempo?
 
Si las respuestas son sí/sí/no, adelante. Si una es no, no uses Claude Code.
 
8 · Cómo comportarte cuando entras a un proyecto LOPs nuevo
 
Smoke test: verifica conexión con un get_project_info o un print básico
Inventario: lista los LOPs ('LOP' in c.tags) y clasifica (agents, tools, etc.)
Leer documentos master del proyecto si existen — pídele al usuario "¿hay un master.md o similar?" antes de inferir
No tocar producción. Si vas a experimentar, copia operadores como *_test y usa Haiku/modelos baratos
Pulsar reinitextensions después de cualquier cambio estructural en un agente
Limpiar tras experimentos. Si añadiste filas de test a tablas reales, bórralas. Si copiaste operadores, destrúyelos o avisa al usuario
No usar Claude Code sin pedir permiso explícitamente
 
 
9 · Apéndice: snippets útiles
9.1 Listar todos los tools que ve un agente
pythonag = op('/project1/agent_XXX')
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
9.2 Tester de una función de módulo en tool_td_mod (sin agente)
pythonimport json
tdm = op('/project1/tool_td_mod1')
 
class MockToolCall:
    def __init__(self, args):
        class _F:
            def __init__(self, a): self.arguments = json.dumps(a)
        self.function = _F(args)
 
# Listar módulos
print(tdm.ext.TDModToolEXT.HandleMod(MockToolCall({"action":"list"})))
 
# Llamar función
result = tdm.ext.TDModToolEXT.HandleMod(MockToolCall({
    "action":"call",
    "function":"<modulo>.<funcion>",
    "args": {"arg1": "valor1"}
}))
print(json.dumps(result, indent=2, default=str))
9.3 Reset session de un agente sin perder configuración
pythonag = op('/project1/agent_XXX')
ag.par.Cancelcall.pulse()
ag.par.Clearsession.pulse()
ag.par.reinitextensions.pulse()
# Resultado: conversación vacía, mismos tools y system_message
9.4 Cost guard antes de probar nada
pythonag = op('/project1/agent_test')
ag.par.Costbudget = 0.05  # 5 céntimos máximo por query
ag.par.Resetcostmeter.pulse()
# Lanza query, si supera $0.05 corta
9.5 Buscar logs útiles de un operador
Cada LOP suele tener un sub-DAT logs (null) con eventos timestampados y categorizados. Útil para diagnóstico:
pythonlog = op('/project1/<op>/logs')
print(f"{log.numRows} entries")
for r in range(max(1, log.numRows-10), log.numRows):
    print([str(log[r,c].val)[:120] for c in range(min(4, log.numCols))])
9.6 Crear un módulo Python para tool_td_mod desde cero
pythonsrc_code = '''"""
mi_modulo - descripción breve.
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
 
# Compilar para verificar sintaxis
compile(src_code, 'mi_modulo', 'exec')
 
# Crear en el comp modules del tool_td_mod
modules_comp = op('/project1/tool_td_mod1/modules')
existing = modules_comp.op('td_mi_modulo')
if existing:
    existing.text = src_code
else:
    dat = modules_comp.create(textDAT, 'td_mi_modulo')
    dat.text = src_code
 
# Verificar que aparece
print(op('/project1/tool_td_mod1').GetTool()['tool_definition']['function']['parameters']['properties']['args']['description'])
9.7 Auto-conectar un servicio externo al abrir el .toe
Algunos LOPs con bridges o conexiones externas (típicamente claude_codeLOP, MCP servers, sockets) no se conectan automáticamente al cargar el proyecto: requieren pulsar Connect a mano cada vez. Patrón general para resolverlo: un executeDAT con start=True (callback onStart) que dispare el pulse necesario. Es idempotente — si ya está conectado, el pulse no hace nada.
python# Crear el executeDAT
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
        # Idempotente: solo conectar si no estaba ya
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
Generalizable a cualquier handshake de arranque: cargar caches, inicializar workers, restablecer suscripciones, etc.
9.8 Watcher event-driven sobre un DAT de log: cómo se hace bien
Patrón completo para vigilar una tabla que crece monotónicamente (como un log) y reaccionar SOLO a filas nuevas que cumplan un criterio. Es el patrón usado para detectar el fin de query de claude_code1 en GIVAH, pero generaliza a cualquier escenario "tail -f con filtro":
python# Crear el watcher
w = op('/project1').create(datexecuteDAT, '<nombre>_watcher')
w.par.language = 'python'
w.par.dat = '/ruta/al/log_dat'        # tabla a vigilar
w.par.tablechange = True
w.par.sizechange = True
w.par.rowchange = True
w.par.active = True
 
w.text = '''
# Watcher event-driven con persistencia via me.storage.
# Procesa SOLO filas añadidas desde la última invocación, filtradas por criterio.
 
def _process_new_rows(dat, n_old, n_new):
    # Identificar columna por header (no por índice — más robusto)
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
            # ... lógica de tu evento ...
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
        # Primera observacion: NO procesar historico
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
 
# Inicializar el contador para no procesar el historico existente
target = op(w.par.dat.eval())
w.store('prev_rows__' + target.path, target.numRows)
Para repuntar el watcher si el DAT objetivo cambia (por ejemplo, otra sesión de un LOP que crea nuevos sub-COMPs), añadir un parameterexecuteDAT que vigile el parámetro fuente y haga:
pythondef onValueChange(par, prev):
    new_path = "/nueva/ruta/calculada/a/partir/de/par"
    watcher = op("/project1/<nombre>_watcher")
    watcher.par.dat = new_path
    # Inicializar contador del nuevo target al numRows actual
    watcher.store("prev_rows__" + new_path, op(new_path).numRows)
Cuidado crítico al testear: los appendRow desde el MCP no disparan los callbacks de este watcher (ver §6.10). Para validar que funciona, lanza una operación real del operador que normalmente escribe en el log, o invoca la función de callback directamente desde MCP saltando el datexec.
 
10 · Recursos externos
 
Doc oficial LOPs: https://docs.dotsimulate.com/ y https://dotdocs.netlify.app/
Mapa visual de operadores: https://docs.dotsimulate.com/map/ — al clicar un operador muestra los relacionados. Pídele al usuario una captura si necesitas ver el contexto de un operador desconocido, ya que no puedes navegar la web desde el MCP
TouchDesigner doc oficial: https://docs.derivative.ca/
dotsimulate Discord: soporte de comunidad para el pack LOPs
 
 
11 · Fin
Este documento es vivo. Si descubres algo nuevo trabajando en un proyecto LOPs, pide al usuario que lo añada aquí antes de cerrar la sesión. La próxima instancia de Claude te lo agradecerá.
