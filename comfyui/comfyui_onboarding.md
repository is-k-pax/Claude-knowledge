# ComfyUI — Onboarding

Setup, instalación, modelos y uso con Claude Desktop via MCP.

**Última revisión:** junio 2026.

---

## Instalación

ComfyUI está instalado via **Pinokio** en el PC principal (framemov).

| Ruta | Descripción |
|---|---|
| `D:\pinokio\api\comfy.git\ComfyUI` | Raíz de ComfyUI |
| `D:\pinokio\api\comfy.git\venv` | Entorno virtual Python (3.11.9) |
| `D:\pinokio\api\comfy.git\app\models` | Modelos (checkpoints, VAE, LoRAs, etc.) |
| `D:\pinokio\api\comfy.git\ComfyUI\custom_nodes` | Nodos personalizados |
| `D:\pinokio\api\comfy.git\ComfyUI\output` | Imágenes generadas |
| `D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\` | Workflows guardados |

**Python ejecutable:** `D:\pinokio\api\comfy.git\venv\Scripts\python.exe`

---

## Arrancar ComfyUI

### Opción 1 — Script local (doble click)
Archivo en el escritorio: `arrancar_comfyui.bat`

```bat
@echo off
D:\pinokio\api\comfy.git\venv\Scripts\python.exe D:\pinokio\api\comfy.git\ComfyUI\main.py --listen 0.0.0.0 --port 8188 --extra-model-paths-config D:\pinokio\api\comfy.git\ComfyUI\extra_model_paths.yaml --database-url sqlite:///D:\pinokio\api\comfy.git\ComfyUI\user\comfyui_standalone.db
pause
```

**IMPORTANTE:** El flag `--extra-model-paths-config` es necesario para que ComfyUI vea todos los modelos en `app\models\`. Sin él solo ve `ae.safetensors` en VAE y no encuentra `flux2-vae.safetensors`.

### Opción 2 — Arranque remoto via SSH (desde PC de casa)
Ver `comfyui/comfyui_remote_setup.md` para el setup completo de SSH + Tailscale.

```powershell
ssh -i "$env:USERPROFILE\.ssh\comfyui_key" framemov@100.102.173.86 "powershell -File C:\Users\framemov\Desktop\arrancar_comfyui_bg.ps1"
```

---

## Workflows guardados

Los workflows están en `D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\`.

Verificar que ComfyUI los ve: `http://127.0.0.1:8188/api/userdata?dir=workflows&recurse=true`

Workflows disponibles:
- `flux2_klein_img2img_editing.json` — Flux 2 Klein img2img con referencia
- `video_wan2_2_14B_i2v.json` — Wan 2.2 14B image-to-video

Ver `comfyui/comfyui_workflows.md` para detalles de uso de cada workflow.

---

## Uso con Claude Desktop (MCP)

ComfyUI se controla desde Claude Desktop via el MCP `comfyui-mcp`.

Config en `claude_desktop_config.json` (PC local, con ComfyUI en localhost):
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

Para uso remoto (desde otro PC), ver `comfyui/comfyui_remote_setup.md`.

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

Los modelos están en `D:\pinokio\api\comfy.git\app\models\` y son visibles via `extra_model_paths.yaml`.

Subcarpetas principales:
- `checkpoints/` — modelos base (Flux, SDXL, SD1.5...)
- `vae/` — VAEs (incluye `flux2-vae.safetensors`, `ae.safetensors`, `wan_2.1_vae.safetensors`)
- `loras/` — LoRAs
- `clip/` — encoders CLIP
- `text_encoders/` — encoders de texto (T5, CLIP-L...)
- `diffusion_models/` — modelos de difusión (formato unet)
- `controlnet/` — modelos ControlNet
- `upscale_models/` — modelos de upscale

Para ver qué hay instalado: `http://127.0.0.1:8188/models/vae` (o cualquier categoría).

---

## Custom nodes instalados

- **ComfyUI-Manager** — gestión de nodos
- **comfyui_controlnet_aux** — preprocesadores ControlNet
- **comfyui-NDI-main** — salida NDI (puede fallar al arrancar, no crítico)
- **websocket_image_save** — guardado via websocket

---

## Notas de uso

- ComfyUI corre en el puerto **8188**
- El flag `--listen 0.0.0.0` es necesario para acceso remoto
- El flag `--extra-model-paths-config` es necesario para ver todos los modelos
- Si falla al arrancar por conflicto de base de datos, usar `--database-url` con ruta alternativa
- Pinokio no funciona para arrancar ComfyUI — usar el `.bat` o SSH remoto
