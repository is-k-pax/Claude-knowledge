# TouchDesigner — Catálogo de operadores LOPs

Guía operativa de los operadores LOPs disponibles.

**Última revisión:** 8 de junio de 2026.

---

## Agent LOP (agentLOP)

Wrapper sobre llamada a LLM. Parámetros clave: `Apiserver`, `Model`, `Systemmessagedat` (lee de `<agent>/system_prompt`, no del DAT directo), `Contextop`, `Sessionmode`, `Maxresultchars` (default 16K, poner 250000 para tablas grandes), `Costbudget`, `Paralleltoolcalls`.

Tool sequence: `agent.seq.Tool.numBlocks = N`. Re-parse: `agent.par.reinitextensions.pulse()`.

## ChatTD

Path: `/dot_lops/ChatTD`. Runtime compartido. Parámetro crítico: Python Venv para SideCars.

## Tool DAT (tool_datLOP)

Operaciones sobre Table/Text DAT. Cada uno necesita `Toolname` único. `Responseverbosity`: usar `full` para lecturas.

## Tool Request LOP — llamada HTTP externa para servicios de imagen, voz, etc.

## Tool Parameter LOP — expone parámetros de un operador como tool.

## Tool TD Mod (tool_td_modLOP) ⭐ recomendado

Módulos Python como tools. 4 actions: `list`, `doc`, `source`, `call`. Mejor que Tool DAT para validación compleja. Módulos starter: `catalog`, `net`, `search`.

## Tool TD Code — Python arbitrario con safety blocking. Reservar para desarrollo.

## Tool VFS (tool_vfsLOP)

Filesystem virtual sandboxed. Setup: `Checkvfs.pulse()` con `Createifmissing=True`.

## Tool Manager (tool_managerLOP) ⭐

Agregador + MCP server. Añadir slot → `Refreshtools.pulse()` → `Restartserver.pulse()`.

## Tool Registry — descubrir y asignar tools a agents.

## Tool Monitor — tracking del USUARIO, no de agentes.

## Tool Op Context — análisis: `quick_summary`, `troubleshoot`, `optimize`, `explain`, `get_content`.

## Agent Swarm — lead+workers con protocolos de coordinación.

## Any (anyLOP) — módulo Python externo simple.

## Context Grabber — agrupa DATs como system message cada turno.

## Chat Viewer — panel UI para debug de conversaciones.
