# ComfyUI — Onboarding

Setup, instalación, modelos y uso con Claude Desktop via MCP.

**Última revisión:** junio 2026.

---

## Instalación

ComfyUI está instalado via **Windows Portable** en el PC principal (vuski — PC nuevo local).

| Ruta | Descripción |
|---|---|
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\ComfyUI` | Raíz de ComfyUI |
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\python_embeded` | Python embebido |
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\ComfyUI\models` | Modelos |
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\ComfyUI\custom_nodes` | Nodos personalizados |
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\ComfyUI\output` | Imágenes y vídeos generados |
| `C:\Users\[username]\Documentos\ComfyUI_windows_portable\ComfyUI\user\default\workflows\` | Workflows guardados |

---

## Arrancar ComfyUI

Doble click en:
```
C:\Users\[username]\Documentos\ComfyUI_windows_portable\run_nvidia_gpu.bat
```

ComfyUI arranca en `http://127.0.0.1:8188` y queda accesible localmente.

**Nota:** Usar `run_nvidia_gpu.bat` para generación con GPU. `run_cpu.bat` solo para pruebas sin GPU.

---

## Workflows guardados

Los workflows están en `ComfyUI\user\default\workflows\`.

Verificar que ComfyUI los ve: `http://127.0.0.1:8188/api/userdata?dir=workflows&recurse=true`

Workflows disponibles (nombres exactos):
- `image_flux2_text_to_image_9b.json` — Flux 2 Klein 9B text to image
- `image_flux2_klein_image_edit_9b_base.json` — Flux 2 Klein 9B img2img / edición
- `video_wan2_2_14B_i2v.json` — Wan 2.2 14B image-to-video
- `Video-Upscaler-Next-Diffusion.json` — Upscale vídeo + interpolación FPS

Ver `comfyui/comfyui_workflows.md` para detalles de uso de cada workflow.

---

## Uso con Claude Desktop (MCP)

ComfyUI se controla desde Claude Desktop via el MCP `comfyui-mcp`.

Config en `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "comfyui": {
      "command": "npx",
      "args": ["-y", "comfyui-mcp"]
    }
  }
}
```

El MCP apunta a `localhost:8188` por defecto. No se necesita configuración adicional con ComfyUI corriendo en local.

---

## Skills instaladas en Claude Desktop

Las siguientes skills están montadas localmente y Claude las lee automáticamente:

| Skill | Descripción |
|---|---|
| `comfyui-core` | Formato de workflows, tipos de nodos, uso del MCP |
| `prompt-engineering` | Sintaxis CLIP, pesos, prompting por modelo |
| `troubleshooting` | Errores OOM, nodos faltantes, imágenes negras |
| `model-compatibility` | Compatibilidad sampler/CFG/VAE por familia de modelo |
| `flux-txt2img` | Workflows Flux.1 Dev, Klein, Turbo LoRAs |
| `model-registry` | URLs de descarga de modelos por familia |
| `installer-packs` | Sistema de packs de instalación |
| `workflow-layout` | Organización visual de workflows en el canvas |
| `comfyui-node-registry` | Publicación de nodos personalizados |

---

## Modelos disponibles

Los modelos están en `ComfyUI\models\`.

Subcarpetas principales:
- `checkpoints/` — modelos base
- `vae/` — VAEs
- `loras/` — LoRAs
- `clip/` — encoders CLIP
- `text_encoders/` — encoders de texto
- `diffusion_models/` — modelos de difusión (formato unet)
- `controlnet/` — modelos ControlNet
- `upscale_models/` — modelos de upscale

Para ver qué hay instalado: `http://127.0.0.1:8188/models/vae` (o cualquier categoría).

---

## Notas de uso

- ComfyUI corre en el puerto **8188** en localhost
- El output de vídeos está en `ComfyUI\output\video\` accesible localmente
- Con instalación local, el upload de imágenes via MCP funciona con rutas Windows directas — no se necesita SCP ni Cowork
