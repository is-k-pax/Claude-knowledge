# ComfyUI — Workflows

Workflows probados y listos para usar. Los JSONs están guardados en:
`D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\`

Para ejecutar un workflow: cargar con `get_workflow`, ajustar parámetros, ejecutar con `enqueue_workflow`.

**Última revisión:** junio 2026.

---

## Cuándo usar Chat vs Cowork

| Tarea | Usar |
|---|---|
| Text to image (sin imagen de entrada) | Chat normal del proyecto comfyUI MCP |
| Img2img o vídeo (con imagen de entrada) | **Cowork** — necesita acceso al sistema de archivos para SCP |
| Upscale + interpolación de vídeo | Chat normal — el vídeo ya está en el PC de ComfyUI |

**Por qué:** El chat normal de Claude Desktop no puede ejecutar comandos locales (SCP). Cowork con "Uso de computadora" activado sí puede ejecutar SCP automáticamente para copiar la imagen al PC de ComfyUI.

---

## Flujo completo imagen → vídeo → upscale

El usuario siempre indica la **resolución final deseada** y la **orientación**. Claude calcula automáticamente las resoluciones intermedias.

### Tabla de resoluciones por paso

| Resultado final | Flux (imagen) | Wan 2.2 (vídeo base) | Upscale target (altura) |
|---|---|---|---|
| Portrait 1080×1920 | 540×960 | 270×480 | 1920 |
| Landscape 1920×1080 | 960×540 | 480×270 | 1080 |
| Cuadrado 1080×1080 | 540×540 | 270×270 | 1080 |
| Portrait 720×1280 | 360×640 | 180×320 | 1280 |
| Landscape 1280×720 | 640×360 | 320×180 | 720 |

**Regla:** Wan 2.2 genera a ¼ de la resolución final (el upscale ×4 hace el resto). Flux genera a ½ de la resolución final para que la imagen de referencia tenga buena calidad.

### Flujo por pasos (hacerlo siempre en este orden)

```
PASO 1 — Generar imagen (Flux)
→ Resolución: según tabla arriba
→ Confirmar con el usuario antes de continuar

PASO 2 — Generar vídeo (Wan 2.2) — desde Cowork
→ upload_image() con la imagen del usuario
→ Resolución: según tabla arriba (¼ de la final)
→ Confirmar con el usuario antes de continuar

PASO 3 — Upscale + interpolación
→ Vídeo ya está en output/video/ del PC de ComfyUI
→ Usar workflow mínimo inline (ver sección Video Upscale)
→ FPS multiplier: 2 (×2 FPS) o 4 (×4 FPS) según lo que pida el usuario
```

**No encadenar los pasos automáticamente** — esperar confirmación del usuario entre pasos.

---

## Cómo subir imágenes a ComfyUI desde el PC de casa

**CRÍTICO:** El MCP de ComfyUI no puede leer rutas Linux ni rutas de uploads internas. La imagen debe estar en la carpeta `input/` de ComfyUI antes de ejecutar el workflow.

### En Cowork (automático)
Usar `mcp__comfyui__upload_image` con la ruta Windows del archivo — sube via HTTP al input/ sin SCP:
```
upload_image(source_path="C:\Users\vuski\...\imagen.png", filename="nombre.png")
```

### En chat normal (manual)
El usuario debe ejecutar el SCP desde PowerShell y confirmar que está hecho.

---

## Cómo entregar el resultado al usuario

### Imágenes
```
1. get_history → obtener el filename del output
2. get_image (filename) → descarga la imagen
3. Presentar inline en el chat
```

**NOTA:** Windows bloquea escritura en `Documents` desde Cowork/Dispatch. No intentar guardar ahí — fallará.

### Vídeos
Los vídeos pesan 20-50MB. Se guardan en el PC de ComfyUI en:
`D:\pinokio\api\comfy.git\ComfyUI\output\video\`

Accesibles via carpeta compartida Tailscale: `\\100.102.173.86\comfyui-output`
(usuario: `framemov`, contraseña: contraseña de Windows del PC de ComfyUI)

---

## Workflows disponibles

| Archivo | Modelo | Uso | Velocidad |
|---|---|---|---|
| `flux2_klein_4b_txt2img.json` | Flux 2 Klein 4B | Text to image | ~30s |
| `flux2_klein_img2img_editing.json` | Flux 2 Klein 4B | Img2img / edición con referencia | ~15s |
| `flux1_dev_txt2img.json` | Flux 1 Dev fp8 | Text to image (clásico) | ~42s |
| `video_wan2_2_14B_i2v.json` | Wan 2.2 14B | Image to video ~5s | ~varios min |
| `video_upscale_interpolate.json` | ESRGAN + RIFE | Upscale vídeo + interpolación FPS | ~varios min |

---

## Flux 2 Klein 4B — Text to Image

**Archivo:** `flux2_klein_4b_txt2img.json`
**Uso:** Generar imágenes desde texto.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-4b-fp8.safetensors` |
| VAE | `flux2-vae.safetensors` |
| CLIP | `qwen_3_4b.safetensors` |

### Qué cambiar para cada generación
1. **Prompt** — nodo `76`, campo `value`
2. **Resolución** — nodos `75:68` (width) y `75:69` (height)
3. **Seed** — nodo `75:73`, campo `noise_seed`

---

## Flux 1 Dev — Text to Image (clásico)

**Archivo:** `flux1_dev_txt2img.json`

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Checkpoint | `flux1-dev-fp8.safetensors` (en `checkpoints/`) |

### Notas
- Usa CheckpointLoaderSimple — solo ve modelos en `checkpoints/`, no en `diffusion_models/`

---

## Flux 2 Klein — Img2Img con referencia

**Archivo:** `flux2_klein_img2img_editing.json`
**Usar desde Cowork** para que el upload sea automático.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-4b-fp8.safetensors` |
| VAE | `flux2-vae.safetensors` ← nombre exacto, no usar `ae.safetensors` |
| CLIP | `qwen_3_4b.safetensors` |

### IMPORTANTE
- Con una sola imagen: poner el mismo archivo en los dos nodos (76 y 81)
- NO usar `ae.safetensors` como VAE
- NO cambiar el modelo por Flux 1 ni Kontext si falla

---

## Wan 2.2 14B — Image to Video

**Archivo:** `video_wan2_2_14B_i2v.json`
**Usar desde Cowork** — necesita subir la imagen vía `upload_image`.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet (low noise) | `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` |
| UNet (high noise) | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` |
| VAE | `wan_2.1_vae.safetensors` |
| CLIP | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` |
| LoRA low noise | `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors` |
| LoRA high noise | `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` |

### Procedimiento completo
```
1. upload_image(source_path=<ruta Windows>, filename=<nombre>) → sube al input/
2. get_workflow → video_wan2_2_14B_i2v.json
3. modify_workflow → nodo 97: nombre del archivo
4. modify_workflow → nodo 93: prompt de movimiento en inglés
5. modify_workflow → nodo 98: width y height según tabla de resoluciones
6. validate_workflow
7. enqueue_workflow
8. get_history → esperar resultado (varios minutos)
9. Decir al usuario que el vídeo está en \\100.102.173.86\comfyui-output\video\
```

### Parámetros clave
| Parámetro | Nodo |
|---|---|
| Imagen de entrada | nodo `97` |
| Prompt positivo (inglés) | nodo `93` |
| Width / Height | nodo `98` |
| Frames (81 = ~5s a 16fps) | nodo `98` |

### Notas
- El prompt negativo (nodo `89`) está vacío — no tocar
- Output en `output/video/` → acceder via `\\100.102.173.86\comfyui-output`

---

## Video Upscale + Interpolación

**Archivo:** `video_upscale_interpolate.json`
**Uso:** Hacer upscale de resolución y aumentar FPS de un vídeo ya generado.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Upscale | `4x_NMKD-Siax_200k.pth` (fotorrealismo) |
| Interpolación | `rife47.pth` (se descarga automáticamente la primera vez) |

### CRÍTICO — NO cargar el JSON guardado para enqueue

El workflow `video_upscale_interpolate.json` tiene nodos de UI (Labels rgthree, display nodes) y conexiones dinámicas de frame_rate que causan `prompt_outputs_failed_validation` al enqueuar via API. **Construir siempre el workflow mínimo inline:**

```json
{
  "1": {"class_type": "VHS_LoadVideoPath", "inputs": {
    "video": "D:\\pinokio\\api\\comfy.git\\ComfyUI\\output\\video\\FILENAME.mp4",
    "force_rate": 0, "custom_width": 0, "custom_height": 0,
    "frame_load_cap": 0, "skip_first_frames": 0, "select_every_nth": 1
  }},
  "2": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["3",0], "image": ["1",0]}},
  "3": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x_NMKD-Siax_200k.pth"}},
  "16": {"class_type": "ImageScaleBy", "inputs": {"upscale_method": "lanczos", "scale_by": SCALE_BY, "image": ["2",0]}},
  "43": {"class_type": "RIFE VFI", "inputs": {
    "ckpt_name": "rife47.pth", "clear_cache_after_n_frames": 50,
    "multiplier": FPS_MULT, "fast_mode": false, "ensemble": true, "scale_factor": 1,
    "frames": ["16",0]
  }},
  "44": {"class_type": "VHS_VideoCombine", "inputs": {
    "frame_rate": OUTPUT_FPS, "loop_count": 0,
    "filename_prefix": "Upscaled_Interpolated_",
    "format": "video/h264-mp4", "pix_fmt": "yuv420p", "crf": 19,
    "save_metadata": true, "trim_to_audio": false,
    "pingpong": false, "save_output": true, "images": ["43",0]
  }}
}
```

### Valores a sustituir

| Vídeo Wan (entrada) | SCALE_BY | FPS_MULT | OUTPUT_FPS |
|---|---|---|---|
| 270×480 → 1080×1920 | 1.0 | 4 | 64 |
| 480×270 → 1920×1080 | 1.0 | 4 | 64 |
| 270×270 → 1080×1080 | 1.0 | 4 | 64 |

**Nota FPS:** RIFE solo acepta multiplicadores enteros. Desde 16fps base: ×2=32fps, ×4=64fps. No se puede obtener exactamente 60fps — usar 64.

### Pitfalls
- **VHS_LoadVideo NO sirve** — solo lee del input/ folder. Los vídeos de Wan están en output/video/. Usar **VHS_LoadVideoPath** con ruta absoluta Windows completa.
- **VHS_VideoCombine con format video/h264-mp4 requiere campos extra**: `pix_fmt`, `crf`, `save_metadata`, `trim_to_audio`. Sin ellos da 400 Bad Request.
- **frame_rate como referencia dinámica falla** en VHS_VideoCombine via API — hardcodear el valor numérico.
- **audio como referencia dinámica falla** si el mp4 fuente no tiene pista de audio (los vídeos de Wan no tienen audio). No conectar el campo audio.

---

## Procedimiento estándar (txt2img)

```
1. get_workflow → nombre.json  ← SIEMPRE usar el JSON guardado
2. modify_workflow → prompt, seed
3. validate_workflow
4. enqueue_workflow
5. get_history → filename
6. get_image → inline en el chat
```

**CRÍTICO:** Nunca construir el workflow desde cero — siempre cargar el JSON guardado. Excepción: video_upscale_interpolate.json (ver sección arriba).
