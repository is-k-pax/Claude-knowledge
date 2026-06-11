# TouchDesigner - Claude Code LOP

Cuando usar (y cuando NO usar) el operador claude_codeLOP en proyectos TD.

**Ultima revision:** junio 2026.

---

## Que es claude_codeLOP

Bridge a la CLI local de Claude Code via WebSocket. Auto-lanza el bridge server, persiste
sesiones, expone tools de Claude Code (Bash, Read, Write, etc.) y opcionalmente tools TD
del proyecto.

COSTE: consume el cap de suscripcion Pro/Max del usuario. El bridge log muestra algo como
"Cost: $0.015505 (subscription)". No es gratis aunque no se cobre por token API.

---

## Tabla de decision: si / no

| Tarea | Usar claude_codeLOP |
|---|---|
| Agente principal de la aplicacion en produccion | NO — caro por suscripcion. Usa Agent LOP + API Anthropic directo |
| Evaluacion rutinaria de un agente | NO — usa el MCP de TD directamente |
| Crear un tool nuevo simple | NO — hazlo via execute_python |
| Refactor grande de una sub-red TD | SI — sesion one-shot |
| Script de migracion de datos / scaffold de N operadores | SI |
| Tool compleja que requiere browsing del filesystem + bash | SI (lidar, generacion de assets, etc.) |
| Generacion de codigo que el usuario va a revisar antes de usar | SI |

Antes de invocar, hazte estas preguntas:
- La tarea cabe en una sesion one-shot (menos de 30 min) o necesita supervision continua?
- El usuario esta OK con consumir su cap de suscripcion?
- Puedes hacerla tu directamente con execute_python en menos tiempo?

Si las respuestas son si/si/no, adelante. Si una es no, no uses Claude Code.

---

## Workflow recomendado

```python
cc = op('/project1/claude_code1')
cc.par.Permissionmode = 'bypassPermissions'  # solo para automatizacion supervisada
cc.par.Workingdir = '/ruta/al/repo'           # NO el .toe folder, un repo aparte
cc.par.Prompt = 'descripcion concreta de la tarea one-shot'
cc.par.Sendquery.pulse()
# Esperar viendo cc.par.Currentsession y cc.op('output_dat')
```

---

## Pitfalls especificos

**Permissionmode por defecto pausa esperando aprobacion humana.**
Para automatizacion sin intervencion, poner `bypassPermissions` explicitamente.
En produccion o con usuarios finales, dejarlo en el modo por defecto.

**Sendinterrupt + Sendquery inmediato puede matar el bridge.**
Si el bridge se cuelga, usar `Launchbridge.pulse()` para reanimar.
NO usar `Connect.pulse()` — no reanima un bridge caido, crea conflicto.

**Prompts largos con reasoning extenso pueden colgarse silenciosamente.**
Vigilar el bridge_log del operador. Si no hay actividad en mas de 2 minutos
con un prompt complejo, probablemente se ha colgado.

**El bridge no se conecta automaticamente al cargar el .toe.**
Necesita `Connect.pulse()` o `Launchbridge.pulse()` al abrir el proyecto.
Ver td_snippets.md (snippet "Auto-conectar un servicio externo") para
automatizarlo con un executeDAT startup.

---

## Checklist antes de invocar

- [ ] La tarea es one-shot y acotada (no necesita supervision continua)
- [ ] Usuario informado del coste de suscripcion
- [ ] Permissionmode configurado segun el contexto
- [ ] Workingdir apuntando a un repo, no al .toe folder
- [ ] bridge_log visible para monitorizar progreso
- [ ] Plan de contingencia si el bridge se cuelga (Launchbridge.pulse())
