# TouchDesigner — Onboarding y conexión

Cómo conectar Claude a un proyecto TouchDesigner via MCP y verificar que todo funciona.

**Última revisión:** 29 de junio de 2026.

---

## 1 · Qué es LOPs

LOPs (Language Operator Pack) es un add-on de dotsimulate para TouchDesigner que añade operadores especializados en construir aplicaciones con LLMs dentro de TD. Son operadores TD nativos con parámetros, conexiones y callbacks — no Python suelto.

Cada operador LOP:
- Tiene la tag `LOP` y otra específica del tipo (`agentLOP`, `tool_managerLOP`, etc.)
- Vive típicamente en `/project1/<nombre>1`
- Tiene una página custom con sus parámetros
- Suele tener un sub-COMP Logger y un sub-DAT `logs` para diagnóstico
- Muchos exponen un método `GetTool()` que devuelve schemas de herramienta

Lo que LOPs resuelve: integrar agentes LLM en pipelines audiovisuales sin escribir un servidor por separado. El agente vive en el mismo grafo que el render, los inputs de mic, los outputs de pantalla.

Doc oficial: https://docs.dotsimulate.com/  
Mapa visual de operadores: https://docs.dotsimulate.com/map/

> ⚠️ Tu modelo de entrenamiento probablemente no conoce LOPs. **NO puedes navegar la web desde dentro de TD** (los MCP tools no acceden a la web). Usa `search_web` si el Tool Manager está disponible.

---

## 2 · Dos interfaces disponibles: MCP LOP + Tool Manager

### MCP LOP (puerto 18555) — siempre disponible

El acceso base. Tools principales:

| Tool | Para qué |
|---|---|
| `get_project_info` | FPS, resolución, nombre del proyecto. Smoke test inicial |
| `list_operators` | Listar hijos de un COMP (por defecto /project1) |
| `get_operator_info` | Parámetros, conexiones, errores de un operador |
| `set_parameter` | Cambiar UN parámetro (value como string) |
| `execute_python` | Ejecuta Python arbitrario en el contexto de TD |
| `read_dat` / `write_dat` | Leer/escribir contenido de un DAT |
| `get_chop_channels` | Canales y valores de un CHOP |

### Tool Manager (puerto 18766) — cuando está configurado

Interface ampliada. Container portátil en `/claude_desktop_tool_manager`.  
Ver `td_tool_manager_setup.md` para instrucciones de setup y lista completa de tools.

| Tool | Para qué |
|---|---|
| `td_code` | Python en TD (sandbox — cambios no persisten entre calls) |
| `network_context` | Python con acceso completo al proyecto (más permisivo) |
| `td_mod` | Módulos curados: catalog, net, search |
| `edit_td_dat_*` | Leer/editar DATs con precisión (str_replace, insert, etc.) |
| `file_tool_*` | Sistema de archivos virtual persistente dentro del container |
| `get_recent_activity` | Ver actividad reciente del usuario en TD |
| `capture_network_screenshot` | Screenshot de la red (requiere Pillow instalado) |
| `search_web` | Búsqueda web via Serper (requiere API key) |
| `ls`, `read`, `create`, `undo` | Navegar y editar la red |

---

## 3 · Verificación al arrancar (primera operación SIEMPRE)

```python
# Smoke test: ¿estamos conectados?
print(f"FPS: {project.cookRate}")
print(f"Operadores en /project1: {len(op('/project1').children)}")

# Inventario LOPs del proyecto
lops = [c.path for c in op('/project1').children if hasattr(c,'tags') and 'LOP' in c.tags]
print(f"LOPs encontrados: {len(lops)}")
for p in lops: print(f"  {p}")

# Verificar si Tool Manager está disponible
tm_container = op('/claude_desktop_tool_manager')
if tm_container:
    tm = op('/claude_desktop_tool_manager/tool_manager1')
    if tm:
        print(f"Tool Manager: {'Running' if tm.par.Running.eval() else 'Stopped'}")
        print(f"Server URL: {tm.par.Serverurl.eval()}")
```

---

## 4 · Comportamiento al entrar a un proyecto LOPs nuevo

1. **Smoke test:** verificar conexión
2. **Verificar si existe `/claude_desktop_tool_manager`** con Tool Manager configurado
   - Si existe y Running=True → 25 tools disponibles via touchdesigner-lop
   - Si existe pero parado → `op('/claude_desktop_tool_manager/tool_manager1').par.Restartserver.pulse()`
   - Si no existe → ofrecerse a crearlo (ver `td_tool_manager_setup.md`)
3. **Inventario:** listar LOPs y clasificar (agents, tools, etc.)
4. **Leer documentos master** — pedir "¿hay un master.md o similar?"
5. **No tocar producción.** Copiar operadores como `*_test`, usar modelos baratos
6. **`reinitextensions`** después de cualquier cambio estructural en un agente
7. **Limpiar tras experimentos.** Borrar filas de test, destruir operadores copiados
8. **No usar Claude Code** sin pedir permiso explícito

---

## 5 · Instalar dependencias para LOPs correctamente

Los LOPs con SideCar corren en un proceso aparte que usa el venv de `ChatTD`. Si haces `pip install` en otro Python, el SideCar no lo verá.

**La forma correcta:**
1. Abrir el operador Python Manager de LOPs
2. Pulsar "Open Console" → terminal con el venv ya activo
3. `uv pip install <paquete>` (LOPs usa UV por defecto)

Si da `[WinError 5] Acceso denegado`:
1. Cerrar TD completamente
2. `taskkill /F /IM python.exe`
3. Reabrir TD → Python Manager → Open Console → instalar

---

## 6 · Recursos externos

- Doc oficial LOPs: https://docs.dotsimulate.com/
- Mapa visual: https://docs.dotsimulate.com/map/
- TD doc oficial: https://docs.derivative.ca/
- dotsimulate Discord: soporte de comunidad
