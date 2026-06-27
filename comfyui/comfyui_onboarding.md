# ComfyUI — Onboarding

Setup, instalación, modelos y uso con Claude Desktop via MCP.

**Última revisión:** junio 2026.

---

## Dos entornos disponibles

| Entorno | PC | Acceso | Cuándo usarlo |
|---|---|---|---|
| **Local** | vuski (PC nuevo) | `localhost:8188` | Por defecto — más rápido, sin latencia |
| **Remoto** | framemov (PC viejo) | Tailscale `100.102.173.86:8188` | Si vuski no está disponible o para comparar |

---

## Entorno LOCAL — vuski

### Rutas

| Ruta | Descripción |
|---|---|
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI` | Raíz de ComfyUI |
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\python_embeded` | Python embebido |
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\models` | Modelos |
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\custom_nodes` | Nodos personalizados |
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\output` | Imágenes y vídeos generados |
| `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\user\default\workflows\` | Workflows guardados |

### Arrancar

Doble click en `C:\Users\vuski\Documents\ComfyUI_windows_portable\run_nvidia_gpu.bat`

ComfyUI arranca en `http://127.0.0.1:8188`.

### MCP config

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

Apunta a `localhost:8188` por defecto — no necesita configuración adicional.

### Upload de imágenes

Con ComfyUI local, `upload_image` funciona con rutas Windows directas. No se necesita SCP ni Cowork.

### Output

Imágenes y vídeos en `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\output\` accesibles localmente.

---

## Entorno REMOTO — framemov

### Rutas

| Ruta | Descripción |
|---|---|
| `D:\pinokio\api\comfy.git\ComfyUI` | Raíz de ComfyUI |
| `D:\pinokio\api\comfy.git\venv` | Entorno virtual Python (3.11.9) |
| `D:\pinokio\api\comfy.git\app\models` | Modelos |
| `D:\pinokio\api\comfy.git\ComfyUI\custom_nodes` | Nodos personalizados |
| `D:\pinokio\api\comfy.git\ComfyUI\output` | Imágenes y vídeos generados |
| `D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\` | Workflows guardados |

### Arrancar (remoto desde vuski via SSH + Tailscale)

Ver `comfyui/comfyui_remote_setup.md` para el setup completo.

```powershell
ssh -i "$env:USERPROFILE\.ssh\comfyui_key" framemov@100.102.173.86 "powershell -File C:\Users\framemov\Desktop\arrancar_comfyui_bg.ps1"
```

**IMPORTANTE:** El flag `--extra-model-paths-config` es necesario para que ComfyUI vea todos los modelos en `app\models\`.

### MCP config (apuntando a framemov)

Ver `comfyui/comfyui_remote_setup.md` — requiere configurar el endpoint remoto en el MCP.

### Upload de imágenes

El MCP `upload_image` **no funciona** con rutas Linux del entorno de Claude. Opciones:
- **Desde Cowork:** `upload_image` con ruta Windows local de vuski
- **Manual:** SCP desde PowerShell, o copiar via carpeta compartida Tailscale `\\100.102.173.86\comfyui-output`

### Output

Vídeos en `\\100.102.173.86\comfyui-output\video\` (usuario: `framemov`, contraseña de Windows del PC).

---

## Workflows guardados

Los mismos workflows están disponibles en ambos entornos (nombres exactos):

- `image_flux2_text_to_image_9b.json` — Flux 2 Klein 9B text to image
- `image_flux2_klein_image_edit_9b_base.json` — Flux 2 Klein 9B img2img / edición
- `video_wan2_2_14B_i2v.json` — Wan 2.2 14B image-to-video
- `Video-Upscaler-Next-Diffusion.json` — Upscale vídeo + interpolación FPS

Ver `comfyui/comfyui_workflows.md` para detalles de uso de cada workflow.

---

## Skills instaladas en Claude Desktop

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

Subcarpetas principales (en ambos entornos):
- `checkpoints/` — modelos base
- `vae/` — VAEs
- `loras/` — LoRAs
- `clip/` — encoders CLIP
- `text_encoders/` — encoders de texto
- `diffusion_models/` — modelos de difusión (formato unet)
- `controlnet/` — modelos ControlNet
- `upscale_models/` — modelos de upscale

Para ver qué hay instalado: `http://127.0.0.1:8188/models/vae` (o la IP remota si es framemov).

---

## Notas de uso

- ComfyUI corre en el puerto **8188** en ambos entornos
- En framemov: el flag `--extra-model-paths-config` es necesario para ver todos los modelos
- En framemov: Pinokio no funciona para arrancar ComfyUI — usar el `.bat` o SSH remoto
