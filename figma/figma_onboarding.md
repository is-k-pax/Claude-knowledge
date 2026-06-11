# Figma MCP — Guía de uso (ClaudeTalkToFigma)

> Este documento explica qué puede hacer Claude cuando está conectado a Figma mediante el MCP `ClaudeTalkToFigma`.

---

## Cómo funciona

Claude se comunica con Figma **a través de un WebSocket local** — no usa la REST API de Figma ni consume el token personal. El plugin actúa como puente entre Claude y el documento abierto en Figma Desktop.

- Solo funciona con **Figma Desktop** (no web).
- Claude solo puede ver y modificar el documento que esté **abierto y activo** en Figma Desktop en ese momento.

---

## Requisitos previos

| Componente | Acción |
|---|---|
| Servidor WebSocket | Ejecutar `npm run socket` en la carpeta de instalación del MCP (puerto 3055 por defecto) |
| Plugin en Figma Desktop | Instalar "Claude Talk to Figma Plugin" desde Plugins → Development |
| MCP configurado | Añadir clave `ClaudeTalkToFigma` en `claude_desktop_config.json` (Claude Desktop) o en `.mcp.json` (Claude Code) |

**Para iniciar una sesión:**
1. Abre una terminal y arranca el servidor WebSocket: `npm run socket`
2. Abre el plugin en Figma Desktop (Plugins → Development → Claude Talk to Figma Plugin)
3. Copia el channel ID (código en verde) y díselo a Claude: `"Conéctate al canal XXXXXXXX"`

> El channel ID cambia cada vez que abres el plugin. Cópialo en el momento.

---

## Lo que Claude puede hacer

### 📖 Lectura / Análisis

| Acción | Descripción |
|---|---|
| `get_document_info` | Información general del documento (nombre, páginas, etc.) |
| `get_pages` | Lista todas las páginas con sus IDs |
| `get_node_info` | Info detallada de un nodo por su ID (posición, tamaño, tipo, hijos) |
| `get_nodes_info` | Igual que el anterior pero para varios nodos a la vez |
| `get_styles` | Todos los estilos locales del documento (colores, texto, efectos) |
| `get_local_components` | Lista todos los componentes locales |
| `get_remote_components` | Componentes de librerías de equipo |
| `get_selection` | Qué tiene seleccionado el usuario en este momento |
| `scan_text_nodes` | Escanea todos los textos dentro de un nodo |
| `get_styled_text_segments` | Segmentos de texto con estilos específicos |
| `get_variables` | Variables y colecciones de variables del documento |
| `get_reactions` | Interacciones/prototipos de un nodo |
| `get_annotation` | Anotaciones de un nodo |
| `get_grid` | Layout grids de un frame |
| `get_guide` | Guías de una página |
| `get_image_from_node` | Metadatos de imagen en un nodo |

### 📥 Exportación de assets

| Acción | Descripción |
|---|---|
| `export_node_as_image` | Exporta un nodo como PNG, JPG, SVG o PDF (con escala configurable) |
| `get_svg` | Devuelve el SVG completo de un nodo como string |

> Para descargar assets Claude necesita el `nodeId` del elemento. Se obtiene con `get_pages` + `get_node_info`, o seleccionando el elemento en Figma y usando `get_selection`.

### ✏️ Creación de elementos

| Elemento | Herramienta |
|---|---|
| Frame | `create_frame` |
| Rectángulo | `create_rectangle` |
| Elipse / círculo | `create_ellipse` |
| Polígono | `create_polygon` |
| Estrella | `create_star` |
| Texto | `create_text` |
| Forma con texto (FigJam) | `create_shape_with_text` |
| Sticky note (FigJam) | `create_sticky` |
| Conector (FigJam) | `create_connector` |
| Componente desde nodo | `create_component_from_node` |
| Set de componentes (variants) | `create_component_set` |
| Instancia de componente | `create_component_instance` |
| Página nueva | `create_page` |

> **Todos los elementos de creación requieren `parentId`** — el ID de la página o frame donde se va a crear. Siempre hay que obtenerlo primero con `get_pages`.

### 🎨 Modificación de estilos

| Acción | Descripción |
|---|---|
| `set_fill_color` | Cambia el color de relleno (RGBA, valores 0–1) |
| `set_stroke_color` | Cambia el color y grosor del borde |
| `set_selection_colors` | Cambia todos los colores de un nodo y sus hijos recursivamente |
| `set_effects` | Sombras, blur, etc. |
| `set_gradient` | Relleno con gradiente |
| `set_corner_radius` | Radio de esquinas |
| `set_image_fill` | Aplica una imagen como relleno (desde URL o base64) |
| `set_image_filters` | Ajustes de brillo, contraste, saturación en imágenes |

### 🔤 Modificación de texto

| Acción | Descripción |
|---|---|
| `set_text_content` | Cambia el contenido de un texto |
| `set_multiple_text_contents` | Cambia varios textos a la vez |
| `set_font_name` | Cambia la fuente |
| `set_font_size` | Cambia el tamaño |
| `set_font_weight` | Cambia el peso (400, 700, etc.) |
| `set_text_align` | Alineación horizontal |
| `set_line_height` | Altura de línea |
| `set_letter_spacing` | Espaciado entre letras |
| `set_paragraph_spacing` | Espaciado entre párrafos |
| `set_text_case` | UPPER / LOWER / TITLE / ORIGINAL |
| `set_text_decoration` | Subrayado, tachado |

### 📐 Transformación y estructura

| Acción | Descripción |
|---|---|
| `move_node` | Mueve un nodo a nueva posición |
| `resize_node` | Redimensiona un nodo |
| `rotate_node` | Rota un nodo (en grados, sentido horario) |
| `set_auto_layout` | Configura auto layout en un frame |
| `group_nodes` | Agrupa nodos |
| `ungroup_nodes` | Desagrupa |
| `boolean_operation` | Unión, sustracción, intersección, exclusión entre formas |
| `flatten_node` | Aplana un nodo (convierte a path) |
| `clone_node` | Clona un nodo existente |
| `delete_node` | Elimina un nodo |
| `rename_node` | Renombra un nodo |
| `reorder_node` | Cambia el orden Z (capas) |
| `insert_child` | Inserta un nodo hijo dentro de un padre |
| `convert_to_frame` | Convierte grupo/shape a frame |
| `set_node_properties` | Visibilidad, bloqueo, opacidad |

### 📄 Gestión de páginas

| Acción | Descripción |
|---|---|
| `create_page` | Crea una página nueva |
| `rename_page` | Renombra una página |
| `duplicate_page` | Duplica una página completa |
| `delete_page` | Elimina una página |

### 🧩 Componentes y variables

| Acción | Descripción |
|---|---|
| `create_component_instance` | Crea una instancia de componente |
| `set_instance_variant` | Cambia la variante de una instancia |
| `detach_instance` | Desvincula una instancia del componente |
| `set_variable` | Crea o actualiza una variable |
| `apply_variable_to_node` | Vincula una variable a una propiedad de nodo |
| `switch_variable_mode` | Cambia el modo de variable en un nodo |

---

## Flujo típico para inspeccionar y descargar assets

```
1. get_pages                             → obtener IDs de páginas
2. get_node_info (nodeId de la página)   → explorar estructura de capas (usar depth para ver hijos)
3. get_selection                         → o seleccionar en Figma y preguntar qué hay
4. export_node_as_image (nodeId, format: "PNG", scale: 2)  → exportar
```

El resultado de `export_node_as_image` es una URL o datos base64. Claude Code puede guardar esos datos a disco usando sus herramientas de sistema de archivos. Ver `figma/figma_export.md` para el flujo completo.

---

## Limitaciones conocidas

- Solo funciona con **Figma Desktop** (no web)
- El WebSocket debe estar corriendo en la terminal durante toda la sesión
- `set_current_page` está **bloqueado** — para crear en una página específica hay que pasar su ID como `parentId`
- En documentos con plan gratuito solo se pueden tener 3 páginas
- No accede a archivos que no estén abiertos en Figma en ese momento
- El channel ID cambia con cada apertura del plugin — hay que obtenerlo de nuevo al iniciar sesión

---

## Configuración en Claude Code (`.mcp.json`)

El archivo correcto para Claude Code es `.mcp.json` en la **raíz del proyecto** (no en `.vscode/mcp.json`, que es para GitHub Copilot).

Para verificar que el MCP está activo: escribe `/mcp` en el panel de Claude Code y comprueba que `ClaudeTalkToFigma` aparece como conectado. Si aparece como "Pending approval", recargar VS Code con `Ctrl+Shift+P → Developer: Reload Window`.
