# ComfyUI — Pitfalls

Errores conocidos y sus soluciones. Consultar antes de iterar por cuenta propia.

**Última revisión:** junio 2026.

---

## Error 400 al enqueue: imagen no encontrada

**Síntoma:**
`Endpoint Bad Request (400 Bad Request): http://100.102.173.86:8188/prompt?clientId=comfyui-mcp`

El mensaje de error del MCP no da detalles. En los logs de ComfyUI aparece:
```
Failed to validate prompt for output 108:
  - Custom validation failed for node: image - Invalid image file: <nombre>.png
```

**Causa:**
El nodo `LoadImage` valida en tiempo de prompt que el archivo exista en el input folder. Si el nombre es incorrecto (typo, mayúsculas, extensión diferente) o el archivo no se subió, falla con 400.

**Fix:**
1. Consultar `get_node_info` para `LoadImage` — devuelve la lista completa de archivos disponibles en el input folder.
2. Buscar el nombre real del archivo (puede haber un typo: `text_moto.png` vs `test_moto.png`).
3. Relanzar con el nombre correcto.

**Nota:** El error 400 aparece ANTES de ejecutar el workflow — es validación de ComfyUI, no un fallo de generación.

---

## El MCP upload_image falla con rutas /mnt/

**Síntoma:**
`ENOENT: no such file or directory, open 'C:\mnt\user-data\uploads\...'`

**Causa:**
El MCP de ComfyUI corre en Windows. Las rutas `/mnt/user-data/uploads/` son de Linux (entorno de Claude) y no existen en Windows.

**Fix:**
Subir la imagen manualmente via SCP desde el PC de casa:
```powershell
scp -i "$env:USERPROFILE\.ssh\comfyui_key" "<ruta_local>" "framemov@100.102.173.86:D:/pinokio/api/comfy.git/ComfyUI/input/<nombre>.png"
```
O subirla directamente desde la web UI de ComfyUI: `http://100.102.173.86:8188`.
