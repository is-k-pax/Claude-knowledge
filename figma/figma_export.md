# Figma Export — Descargar assets de Figma a disco

> Cómo Claude Code puede descargar assets de Figma directamente al sistema de archivos del proyecto, sin usar la REST API ni ningún token personal.

---

## El flujo

```
Plugin Figma Desktop → WebSocket (puerto 3055) → base64 → PNG en disco
```

Un script Node.js (`scripts/figma-export.js`) en el proyecto automatiza este flujo. Claude Code edita el script con los nodos que se quieren exportar y lo ejecuta.

---

## Requisitos

1. **Servidor WebSocket corriendo** (ver `figma_onboarding.md`)
2. **Plugin abierto en Figma Desktop** — anotar el channel ID (código verde)
3. **MCP `ClaudeTalkToFigma` activo** en Claude Code (`.mcp.json` en raíz del proyecto)

---

## El script `scripts/figma-export.js`

Estructura mínima del script:

```js
const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');

const CHANNEL_ID = 'XXXXXXXX';   // ← ID activo del plugin (cambia cada sesión)
const EXPORTS = [
  { nodeId: '125:1792', destino: 'apps/mi-app/public/assets/ui/elemento.png' },
  { nodeId: '125:1954', destino: 'apps/mi-app/public/assets/ui/otro.png' },
  // Añadir tantos nodos como se necesiten
];

// ... lógica de conexión WebSocket, solicitud export_node_as_image,
// decodificación base64 y escritura en disco
```

**Antes de ejecutarlo:** editar `CHANNEL_ID` con el canal activo y `EXPORTS` con los nodos y rutas destino.

---

## Cómo encontrar el nodeId de un elemento

**Método 1 — Desde Claude Code con el MCP:**
```
Conéctate al canal XXXXXXXX y haz get_pages para listar las páginas.
Luego get_node_info del nodo que me interesa.
```

**Método 2 — Desde Figma Desktop:**
1. Selecciona el elemento en Figma
2. Clic derecho → "Copy/Paste as" → "Copy link"
3. El nodeId aparece en la URL como `node-id=125-1792` → se escribe `125:1792`

---

## Cómo pedirle la exportación a Claude Code

```
Ejecuta el script scripts/figma-export.js para exportar estos nodos:
  NODEID_1 → ruta/destino/archivo.png
  NODEID_2 → ruta/destino/archivo.png
Canal activo: XXXXXXXX
```

Claude Code editará el script con los nuevos valores y lo ejecutará.

---

## Qué NO funciona (para no repetir errores)

- ❌ **REST API de Figma** — requiere token personal con límites severos en plan gratuito. No usar para exportación masiva.
- ❌ **Claude Desktop descargando a disco** — Claude Desktop (el chat) no tiene acceso al sistema de archivos local. Solo puede leer Figma. Es Claude Code quien escribe en disco.
- ❌ **`.vscode/mcp.json`** — ese formato es para GitHub Copilot. El archivo correcto para Claude Code es `.mcp.json` en la raíz del proyecto.
- ❌ **Capas ocultas en Figma** — `export_node_as_image` sobre una capa oculta devuelve imagen vacía. Hacerla visible antes de exportar.
- ❌ **Nodos componente/instancia de librería** — pueden exportar 1×1px. Buscar el grupo padre que contiene el visual renderizado.

---

## Pitfalls de coordenadas (para posicionar assets en la app)

- Las coordenadas que devuelve `get_node_info` son **absolutas** (relativas al canvas). Para posicionar en un frame hay que restar el origen del frame: `localX = absoluteX - frameOriginX`.
- `localPosition` reportado por el MCP puede ser inexacto si el nodo tiene rotación en el bounding box — contrastar siempre con `absoluteBoundingBox`.
- **Child order en Figma**: el primer hijo es la capa inferior, el último es la capa superior (opuesto a la intuición de JSX/HTML).

---

## Troubleshooting

**El script no conecta:**
- Verificar que el servidor WebSocket está corriendo: abrir `http://localhost:3055/status` en el navegador.
- Si el puerto 3055 da error de "ya en uso", es que hay una instancia corriendo — está bien.

**El channel ID no funciona:**
- El channel ID cambia cada vez que se abre el plugin. Copiar el código verde que aparece en el plugin en ese momento.

**Claude Code no ve las herramientas de Figma:**
- Escribir `/mcp` en el panel de Claude Code y verificar que `ClaudeTalkToFigma` aparece como conectado.
- Si aparece como "Pending approval": `Ctrl+Shift+P → Developer: Reload Window`.
