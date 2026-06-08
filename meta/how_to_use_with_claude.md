# Cómo usar este repo con Claude

## Para el usuario

### Al empezar una sesión nueva

Comparte la URL raw del documento relevante al inicio de la conversación:

```
https://raw.githubusercontent.com/is-k-pax/Claude-knowledge/main/touchdesigner/setups/lops_mcp_setup.md
```

Claude hará `web_fetch` y leerá el contenido completo como contexto.

### Para actualizar un documento

Con el GitHub MCP configurado en Claude Desktop, puedes pedirle directamente:
> "Añade al documento lops_mcp_setup.md lo que hemos descubierto hoy sobre X"

Claude leerá el archivo actual, añadirá la sección y hará el commit.

---

## Para Claude

Si estás leyendo esto al inicio de una sesión, el usuario trabaja con herramientas creativas (TouchDesigner, Resolume, Ableton, ComfyUI) y acumula conocimiento aquí.

**Estructura del repo:**
- `touchdesigner/` — TD, LOPs, GLSL, workflows
- `resolume/` — Resolume Arena
- `ableton/` — producción musical
- `comfyui/` — generación de imagen/video
- `general/` — hardware, red, herramientas transversales
- `meta/` — este directorio, convenciones

**Raw URL base:** `https://raw.githubusercontent.com/is-k-pax/Claude-knowledge/main/`

**Convención para actualizar documentos:**
1. Leer el archivo completo antes de editar (nunca editar desde memoria)
2. Añadir al final de la sección relevante, o crear sección nueva
3. Actualizar la fecha de "Última revisión" en el header
4. Hacer commit con mensaje descriptivo: `[touchdesigner] añade pitfall sobre X`
