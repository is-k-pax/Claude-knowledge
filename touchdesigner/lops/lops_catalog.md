# LOPs (dotsimulate) — Catálogo de operadores

Doc oficial: https://docs.dotsimulate.com  
**Última revisión:** 29 junio 2026 — 88 operadores activos

> **Nota:** este archivo es un resumen de lectura rápida. Para doc detallada de un op específico, usar `search_web` con `site:docs.dotsimulate.com <nombre_op>`.

---

## Protocolo clave: GetTool()

Todo op LOPs que expone herramientas implementa `GetTool()`.  
El **Agent** las descubre y llama via su Tool sequence.  
El **Tool Manager** agrega múltiples ops y los expone como servidor MCP único.

---

## CONTROLLERS — los que hacen cosas

| Op | Versión | Para qué |
|---|---|---|
| **agent** | v2.0 | Principal. Envía prompts a LLMs, gestiona tool calls, streaming. Multi-provider via LiteLLM. 4 outputs: conversation_dat, output_dat, history_table, turn_table |
| **agent_swarm** | v1.0 | Lead agent + roster de workers. El lead delega via tool calls |
| **agent_scheduler** | v1.0 | Timer que dispara un Agent periódicamente |
| **tool_manager** | v1.1 | Agrega tools de múltiples ops → servidor MCP (puerto 18766). Requiere ChatTD |
| **tool_dat** | v2.4 | Leer/editar DATs desde un agente |
| **tool_td_code** | v1.0 | Ejecutar Python en TD desde un agente |
| **tool_td_mod** | v1.0 | Módulos curados: catalog, net, search |
| **tool_vfs** | v1.1 | Sistema de archivos virtual para agentes |
| **tool_op_context** | v1.0 | Contexto de ops (parámetros, conexiones, estado) |
| **tool_monitor** | v1.3 | Screenshots de TOPs, inspección de nodos |
| **tool_parameter** | v1.3 | Exponer parámetros de ops específicos a agentes. Requiere configuración por op — NO genérico |
| **tool_debugger** | v1.0 | Inspeccionar schemas de tools. Solo para debug |
| **tool_registry** | v1.0 | Registro centralizado de tools en la red |
| **tool_request** | v1.0 | Gestionar invocaciones individuales de tools |
| **mcp_client** | v1.4 | Conectar a servidores MCP externos. Una conexión puede exponer docenas de tools |
| **mcp_server** | v2.3 | Servidor MCP dentro de TD. Para Claude Code, Cursor, etc. |
| **any** | v1.0 | Host dinámico: apunta a un módulo Python y reconstruye tools alrededor |
| **prompt** | v1.0 | Componer bloques DAT en un prompt estable |
| **flow_controller** | v0.2 | Orquestador multi-step. Gestiona un COMP como proceso con pasos |
| **flow_action** | v1.0 | Señal CHOP → dispara transición en FlowController |
| **flow_router** | v1.0 | Tabla-driven dispatcher: matchea eventos → los enruta |
| **flow_state** | v1.0 | Observer pasivo de FlowController. Log de eventos |
| **build_agent_profile** | v1.0 | Convierte un Agent configurado en JSON reutilizable |
| **build_agent_skill** | v1.0 | Convierte un tool op en "agent skill" reutilizable |
| **claude_code** | v2.2 | Bridge WebSocket entre TD y Claude Code CLI |
| **voice_agent** | v1.0 | Agente con STT + TTS integrados |
| **web_viewer** | v1.0 | Visor web embebido en TD |

---

## MODIFIERS — transforman conversaciones

| Op | Para qué |
|---|---|
| **chat** | Conversación multi-turn desde el panel de parámetros |
| **chat_session** | Múltiples Agents en rotación round-robin |
| **chat_viewer** | Renderiza conversaciones con browser embebido |
| **context_grabber** | Recolecta contexto multimodal: TOPs + DATs + snippets |
| **add_message** | Inyecta un mensaje (user/assistant/system) en una conversation table |
| **feedback** | Copia estado de conversación desde tabla referenciada. Reset simple |
| **handoff** | Router inteligente: LLM decide a qué Agent especializado derivar |
| **hold_chat** | Gatekeeper: bloquea o deja pasar según tokens/condiciones |
| **role_creator** | Genera system prompts de producción via meta-arquitectura |
| **summarize** | Resumen en 4 estilos: breve, detallado, bullets, action items |
| **redefine_roles** | Reasigna roles en conversation table |
| **file_in / file_out** | Cargar/guardar conversaciones a disco |
| **safety_check** | Detectar contenido dañino (toxicidad, profanidad) |
| **sentiment** | Análisis de sentimiento en conversaciones |
| **translate** | Traducción local via argostranslate (sin API) |
| **super_select** | Select DAT mejorado con filtrado flexible |
| **caption** | Describir imágenes (TOP → texto) via LLM con visión |

---

## PIPELINES — generación multimedia

| Op | Para qué |
|---|---|
| **stt** | Speech-to-text, providers intercambiables |
| **tts** | Text-to-speech, providers locales y cloud |
| **voice_activity** | Detectar inicio/fin de habla en micrófono |
| **comfyui** | Bridge TD ↔ ComfyUI |
| **geminiimagegen** | Generación de imágenes con Gemini |
| **fal_ai** | Imagen/vídeo con fal.ai |
| **florence** | Visión local: caption, OCR, detección (Microsoft Florence-2) |
| **acestep** | Música text-to-music (ACE-Step) |
| **lyria** | Música continua via Lyria Realtime API de Google (→ CHOP) |
| **ocr** | Extracción de texto de imágenes |
| **scope_controller** | Vídeo AI en tiempo real via Daydream Scope |

---

## RETRIEVERS — fuentes de información

| Op | Para qué |
|---|---|
| **search** | Búsqueda web unificada multi-backend |
| **search_rag** | Índice vectorial de documentos + búsqueda semántica |
| **search_text** | Índice BM25 (léxico, sin GPU) |
| **search_merge** | Combina resultados de múltiples retrievers |
| **graph** | Grafo de relaciones. Nodos, edges, queries híbridas. Requiere Storage backend |
| **serper_search** | Búsqueda web directa via Serper |
| **source_dat** | DAT existente como fuente de documentos |
| **source_docs** | Documentación HTML offline de TD. Requiere BeautifulSoup |
| **source_ops** | Ops de la red TD como fuente |
| **source_github** | Repo GitHub como fuente |
| **source_crawl4ai** | Crawl de URLs web |
| **source_webscraper** | Scraping genérico |
| **save_sources** | Convierte filas de tabla → archivos Markdown en disco |

---

## SETTINGS — infraestructura del sistema

| Op | Para qué |
|---|---|
| **chattd** | **⭐ NÚCLEO.** API keys, modelos, asyncio, logs globales. Sin él nada funciona |
| **storage** | Ubicación compartida en disco para persistencia de LOPs |
| **python_manager** | Gestiona venvs Python, instala paquetes via pip/UV |
| **mcp_config** | Hub central para conexiones MCP (externas e internas) |
| **tdasyncio** | Loop asyncio dentro de TD |
| **web_server** | Servidor HTTP centralizado para LOPs |
| **log_receiver** | Centraliza logs de todos los ops LOPs |
| **token_count** | Estima tokens (costes, control de context window) |
| **settings_ui** | Panel de configuración central con pestañas |
| **activity_viz** | Visualiza actividad de agentes/tools en tiempo real |
| **autosave** | Guardado automático del proyecto |
| **sidecar** | Gestiona procesos Python standalone fuera de TD |
| **check_lop_install** | Verifica dependencias Python instaladas |
| **tox_updater** | Gestiona actualizaciones de .tox desde el registro dotsimulate |

---

## Flujo típico de un proyecto LOPs

```
ChatTD  ←── API keys, modelo, asyncio
  └── Agent ← Prompt / Chat / Chat Session
        ├── Tools: Tool DAT, Tool VFS, Tool TD Code, Tool Manager, MCP Client...
        ├── Context: Context Grabber, Add Message
        ├── Retrievers: Search RAG, Search, Graph...
        └── Output → Chat Viewer / File Out / CHOP outputs
```
