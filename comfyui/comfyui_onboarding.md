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

**Python ejecutable:** `D:\pinokio\api\comfy.git\venv\Scripts\python.exe`

---

## Arrancar ComfyUI

### Opción 1 — Script local (doble click)
Archivo en el escritorio: `arrancar_comfyui.bat`

Contenido:
```bat
@echo off
D:\pinokio\api\comfy.git\venv\Scripts\python.exe D:\pinokio\api\comfy.git\ComfyUI\main.py --listen 0.0.0.0 --port 8188 --database-url sqlite:///D:\pinokio\api\comfy.git\ComfyUI\user\comfyui_standalone.db
pause
```

### Opción 2 — Arranque remoto via SSH (desde PC de casa)
Ver `comfyui/comfyui_remote_setup.md` para el setup completo de SSH + Tailscale.

Comando desde PC de casa:
```powershell
ssh -i "$env:USERPROFILE\.ssh\comfyui_key" framemov@100.102.173.86 "powershell -WindowStyle Hidden -File C:\Users\framemov\Desktop\arrancar_comfyui.ps1"
```

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

Los modelos están en `D:\pinokio\api\comfy.git\app\models\`.

Subcarpetas principales:
- `checkpoints/` — modelos base (Flux, SDXL, SD1.5...)
- `vae/` — VAEs
- `loras/` — LoRAs
- `clip/` — encoders CLIP
- `text_encoders/` — encoders de texto (T5, CLIP-L...)
- `diffusion_models/` — modelos de difusión (formato unet)
- `controlnet/` — modelos ControlNet
- `upscale_models/` — modelos de upscale

Para ver qué hay instalado, pedir a Claude: *"lista los modelos disponibles"*.

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
- Si falla al arrancar por conflicto de base de datos, usar el flag `--database-url` con una ruta alternativa
- Pinokio no funciona para arrancar ComfyUI — usar el `.bat` o SSH remoto
