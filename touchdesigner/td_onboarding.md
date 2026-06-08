# TouchDesigner — Onboarding y conexión

Cómo conectar Claude a un proyecto TouchDesigner via MCP y verificar que todo funciona.

**Origen:** experiencia acumulada en proyectos con LOPs (dotsimulate), mayo-junio 2026.  
**Última revisión:** 8 de junio de 2026.

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

Doc oficial: https://docs.dotsimulate.com/ y https://dotdocs.netlify.app/  
Mapa visual de operadores: https://docs.dotsimulate.com/map/

> ⚠️ Tu modelo de entrenamiento probablemente no conoce LOPs. **NO puedes navegar la web desde dentro de TD** (los MCP tools no acceden a la web). Pide al usuario los textos de doc si los necesitas.

---

## 2 · El MCP touchdesigner-lop

El usuario te conecta a su proyecto a través de un servidor MCP. Tools principales:

| Tool | Para qué |
|---|---|
| `get_project_info` | FPS, resolución, nombre del proyecto. Smoke test inicial |
| `list_operators` | Listar hijos de un COMP (por defecto /project1) |
| `get_operator_info` | Parámetros, conexiones, errores de un operador |
| `set_parameter` | Cambiar UN parámetro (value como string) |
| `execute_python` | Tu herramienta principal. Ejecuta Python arbitrario en el contexto de TD |
| `read_dat` / `write_dat` | Leer/escribir contenido de un DAT |
| `get_chop_channels` | Canales y valores de un CHOP |

Si tienes el MCP de Anthropic (`touchdesigner:`) también tienes `execute_python_script` con modos read-only/safe-write/full-exec y `get_exec_log` para auditar lo que has hecho.

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
```

Si funciona, estás dentro. Si falla: "no tengo conexión con TD, ¿puedes verificar que el servidor MCP está activo?".

---

## 4 · Comportamiento al entrar a un proyecto LOPs nuevo

1. **Smoke test:** verificar conexión
2. **Inventario:** listar LOPs y clasificar (agents, tools, etc.)
3. **Leer documentos master** — pedir "¿hay un master.md o similar?"
4. **No tocar producción.** Copiar operadores como `*_test`, usar Haiku
5. **`reinitextensions`** después de cualquier cambio estructural en un agente
6. **Limpiar tras experimentos.** Borrar filas de test, destruir operadores copiados
7. **No usar Claude Code** sin pedir permiso explícito

---

## 5 · Instalar dependencias para LOPs correctamente

Los LOPs con SideCar corren en un proceso aparte que usa el venv de `ChatTD.par.Python Venv`. Si haces `pip install` en otro Python, el SideCar no lo verá.

**La forma correcta:**
1. Abrir el operador Python Manager
2. Pulsar "Open Console" → terminal con el venv ya activo
3. `pip install <paquete>`

Si pip da `[WinError 5] Acceso denegado`:
1. Cerrar TD completamente
2. `taskkill /F /IM python.exe`
3. Reabrir TD → Python Manager → Open Console → pip install

---

## 6 · Recursos externos

- Doc oficial LOPs: https://docs.dotsimulate.com/ y https://dotdocs.netlify.app/
- Mapa visual: https://docs.dotsimulate.com/map/
- TD doc oficial: https://docs.derivative.ca/
- dotsimulate Discord: soporte de comunidad
