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
→ SCP de la imagen al input de ComfyUI
→ Resolución: según tabla arriba (¼ de la final)
→ Confirmar con el usuario antes de continuar

PASO 3 — Upscale + interpolación — desde chat normal
→ Vídeo ya está en output/video/ del PC de ComfyUI
→ Target height: según tabla arriba
→ FPS multiplier: 2 (×2 FPS) o 4 (×4 FPS) según lo que pida el usuario
```

**No encadenar los pasos automáticamente** — esperar confirmación del usuario entre pasos. El vídeo puede tardar varios minutos y si algo falla es mejor saberlo antes de continuar.

---

## Cómo subir imágenes a ComfyUI desde el PC de casa

**CRÍTICO:** El MCP de ComfyUI no puede leer rutas Linux (`/mnt/user-data/uploads/`) ni rutas de usuario de Windows. La imagen debe estar en la carpeta `input/` de ComfyUI antes de ejecutar el workflow.

### En Cowork (automático)
Claude puede ejecutar SCP automáticamente:
```powershell
scp -i "$env:USERPROFILE\.ssh\comfyui_key" "<ruta_imagen_local>" "framemov@100.102.173.86:D:/pinokio/api/comfy.git/ComfyUI/input/<nombre_archivo>"
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
**Usar desde Cowork** para que el SCP sea automático.

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
**Usar desde Cowork** — necesita SCP para subir la imagen.

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
1. SCP → imagen al input de ComfyUI (Cowork lo hace automático)
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
**Usar desde chat normal** — el vídeo ya está en el PC de ComfyUI, no hace falta SCP.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Upscale | `4x_NMKD-Siax_200k.pth` (fotorrealismo) |
| Interpolación | `rife47.pth` (se descarga automáticamente la primera vez) |

### Parámetros clave
| Parámetro | Nodo | Valores |
|---|---|---|
| Vídeo de entrada | nodo `1`, campo `video` | nombre del archivo en `output/video/` |
| Modelo de upscale | nodo `3`, campo `model_name` | `4x_NMKD-Siax_200k.pth` |
| Resolución target (altura) | nodo `27`, campo `a` | 1920 (portrait), 1080 (landscape) |
| FPS multiplier | nodo `42`, campo `value` | 2 = doblar FPS, 4 = cuadruplicar |
| Multiplicador upscale | nodo `26`, campo `b` | 4 (siempre, modelo es 4x) |

### Procedimiento completo
```
1. get_history → obtener nombre del vídeo generado (en output/video/)
2. get_workflow → video_upscale_interpolate.json
3. modify_workflow → nodo 1: video = nombre del archivo
4. modify_workflow → nodo 27: a = resolución target según tabla
5. modify_workflow → nodo 42: value = FPS multiplier (2 o 4)
6. validate_workflow
7. enqueue_workflow
8. Esperar resultado — output en output/ con prefijo Upscaled_Interpolated_
```

### Notas
- El Face Enhancer está en bypass — no activarlo (no tienes codeformer.pth)
- Con vídeos largos o poca VRAM, activar Meta Batch Manager (nodo `4`) y bajar `frames_per_batch`
- `rife47.pth` se descarga automáticamente la primera vez

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

**CRÍTICO:** Nunca construir el workflow desde cero — siempre cargar el JSON guardado.
