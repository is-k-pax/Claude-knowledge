# LOPs — Router

LOPs (Language Operator Pack) = operadores de dotsimulate para construir
aplicaciones LLM dentro de TouchDesigner. No los conoces de entrenamiento.
Doc oficial: https://docs.dotsimulate.com/

## Qué documento leer según la situación

| Situación | Lee |
|---|---|
| Qué operadores LOPs existen y para qué | lops_catalog.md |
| Algo falla en LOPs o Tool Manager | lops_pitfalls.md **y lops_pitfalls_2.md** |
| Skills de agente (build_agent_skill, skills_config, portabilidad) | lops_pitfalls_2.md (sección Build Agent Skill) |
| Código LOPs reutilizable (snippets) | lops_snippets.md |
| Speech-to-text o text-to-speech | lops_stt_tts.md |
| Usar Claude Code LOP | lops_claude_code.md |
| Configurar Tool Manager desde cero | lops_tool_manager.md |
| Exponer un tool_manager a un cliente MCP externo (ChatGPT, etc.) | lops_external_mcp_exposure.md |
| Buscar documentación sobre el funcionamiento de un operador de TD | leer_documentacion.md |
| Trabajar con operadores POPX | ../popx/popx_router.md |

---

## Al entrar a un proyecto TD con LOPs — hazlo en este orden

1. **Smoke test** — verificar conexión:
```python
# Desde network_context o td_code:
print(f"FPS: {project.cookRate}")
print(f"Ops en /project1: {len(op('/project1').children)}")
```

---

## Tools del Tool Manager — las que usarás para trabajar

El Tool Manager expone ~25 tools via MCP (puerto 18766).
Estas son las que necesitas conocer, por orden de uso:

### Para construir y diagnosticar (las más usadas)

| Tool | Para qué | Cuidado |
|---|---|---|
| `network_context` | Python que **persiste** — crear ops, conectar, modificar la red real | Usar para cambios estructurales |
| `td_code` | Python en **sandbox** — inspeccionar, leer, probar | Cambios NO persisten entre calls |
| `td_mod` | Módulos curados: `catalog` (tipos de op), `net` (leer red), `search` (descubrir módulos) | action: list/doc/source/call |
| `edit_td_dat_*` | Editar DATs con precisión | Flujo: set_target → read_content → insert/str_replace |
| `ls` | Listar hijos de un COMP | Sin path = raíz del proyecto |
| `read` | Leer archivo o DAT con números de línea | Usar view_range para archivos grandes |
| `capture_network_screenshot` | Screenshot de la red | Requiere Pillow en el venv |
| `get_recent_activity` | Ver qué ha tocado el usuario recientemente | — |

**Peculiaridad del sandbox de estos tools:** funciones anidadas y comprehensions no ven las
variables definidas en el propio script (globals/locals separados de `exec`) — escribir todo
plano. Detalle en lops_pitfalls_2.md.

---

## Diferencia clave: network_context vs td_code

- **`network_context`**: Python con acceso completo al proyecto. Los operadores que
  crees, las conexiones que hagas, los parámetros que cambies → **persisten en la red real de TD**.
  Usar para cualquier cambio que deba quedarse.

- **`td_code`**: Python en sandbox aislado. Variables y operadores creados aquí
  **desaparecen al terminar el call**. Usar para inspección, lectura, pruebas rápidas.

Si te piden "crea un operador" o "conecta X con Y" → `network_context`.
Si te piden "mira qué hay en X" o "comprueba el valor de Y" → cualquiera de los dos vale.

---

## Reglas de conducta en proyectos LOPs

- Tras cambios en tools o system_message de un agente: `reinitextensions.pulse()`
- Copiar ops LOPs entre containers: usar `save()` + `loadTox()`, NO `copy()` (va al src)
- No usar Claude Code LOP sin pedir permiso explícito al usuario
- Limpiar tras experimentos: borrar filas de test, destruir operadores copiados
