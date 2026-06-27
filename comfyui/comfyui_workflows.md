# ComfyUI — Workflows

Workflows probados y listos para usar. Los JSONs están guardados en:
`ComfyUI\user\default\workflows\`

Para ejecutar un workflow: cargar con `get_workflow`, ajustar parámetros, ejecutar con `enqueue_workflow`.

**Última revisión:** junio 2026.

---

## Cuándo usar Chat vs Cowork

La única razón para usar Cowork es **subir una imagen de referencia al `input/` de ComfyUI cuando éste corre en una máquina remota** (framemov). Con ComfyUI local (vuski) todo va por chat normal.

| Tarea | vuski (local) | framemov (remoto) |
|---|---|---|
| Text to image | Chat normal | Chat normal |
| Img2img con imagen de referencia | Chat normal — `upload_image` con ruta local | **Cowork** — necesita SCP para copiar la imagen |
| Wan 2.2 i2v con imagen de referencia | Chat normal — `upload_image` con ruta local | **Cowork** — necesita SCP para copiar la imagen |
| Upscale + interpolación de vídeo | Chat normal — vídeo ya en output/ local | Chat normal — vídeo ya en output/ de framemov |

**Por qué:** `upload_image` del MCP necesita una ruta Windows accesible desde el PC donde corre el MCP (vuski). Si ComfyUI está en framemov (otra máquina), la imagen tiene que llegar allí via SCP — un comando de terminal que solo Cowork puede ejecutar automáticamente.

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

PASO 2 — Generar vídeo (Wan 2.2)
→ El usuario indica qué imagen usar (nombre del output o ruta local)
→ Resolución: según tabla arriba (¼ de la final)
→ Confirmar con el usuario antes de continuar

PASO 3 — Upscale + interpolación
→ Vídeo ya está en ComfyUI/output/video/
→ Usar workflow mínimo inline (ver sección Video Upscale)
→ FPS multiplier: 2 (×2 FPS) o 4 (×4 FPS) según lo que pida el usuario
```

**No encadenar los pasos automáticamente** — esperar confirmación del usuario entre pasos.

---

## Cómo subir imágenes a ComfyUI (img2img / i2v)

### vuski (local)

`upload_image` funciona directamente con rutas Windows:

```
upload_image(source_path="C:\\Users\\vuski\\Documents\\...\\imagen.png", filename="nombre.png")
```

La imagen queda en `ComfyUI/input/` y se referencia por nombre en el nodo `LoadImage`.

### framemov (remoto)

`upload_image` no puede leer rutas Linux del entorno de Claude. Opciones:
- **Cowork (automático):** ejecuta SCP desde PowerShell para copiar la imagen de vuski a framemov
- **Manual:** el usuario copia la imagen a `\\100.102.173.86\comfyui-output\input\` y confirma

---

## Cómo entregar el resultado al usuario

### Imágenes
```
1. get_history → obtener el filename del output
2. convert_image (jpeg, quality 75-80) → reducir tamaño
3. view_image → mostrar inline en el chat
```

### Vídeos
Los vídeos se guardan en `ComfyUI\output\video\`.
- **vuski:** accesibles directamente en `C:\Users\vuski\Documents\ComfyUI_windows_portable\ComfyUI\output\video\`
- **framemov:** accesibles via `\\100.102.173.86\comfyui-output\video\`

---

## Workflows disponibles

| Archivo (nombre exacto) | Modelo | Uso | Velocidad |
|---|---|---|---|
| `image_flux2_text_to_image_9b.json` | Flux 2 Klein 9B | Text to image | ~30s |
| `image_flux2_klein_image_edit_9b_base.json` | Flux 2 Klein 9B | Img2img / edición con referencia | ~15s |
| `video_wan2_2_14B_i2v.json` | Wan 2.2 14B | Image to video ~5s | ~varios min |
| `Video-Upscaler-Next-Diffusion.json` | ESRGAN + RIFE | Upscale vídeo + interpolación FPS | ~varios min |

---

## Flux 2 Klein 9B — Text to Image

**Archivo:** `image_flux2_text_to_image_9b.json`
**Uso:** Generar imágenes desde texto. Es un subgraph — el nodo exterior es `75`.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-base-9b-fp8.safetensors` |
| CLIP | `qwen_3_8b_fp8mixed.safetensors` |
| VAE | `full_encoder_small_decoder.safetensors` |

### Qué cambiar para cada generación
1. **Prompt** — nodo subgraph `75`, input `text` (proxy del nodo interno `74`)
2. **Resolución** — inputs `value` (width) y `value_1` (height) del nodo `75`
3. **Seed** — input `noise_seed` del nodo `75`
4. **Modelos** — inputs `unet_name`, `clip_name`, `vae_name` del nodo `75`

### Procedimiento
```
1. get_workflow → image_flux2_text_to_image_9b.json
2. modify_workflow → prompt, resolución, seed
3. validate_workflow
4. enqueue_workflow
5. get_history → filename
6. convert_image (jpeg, 75) → view_image
```

---

## Flux 2 Klein 9B — Img2Img / Edición con referencia

**Archivo:** `image_flux2_klein_image_edit_9b_base.json`
**Uso:** Editar o transformar una imagen existente usando otra como referencia.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-base-9b-fp8.safetensors` |
| CLIP | `qwen_3_8b_fp8mixed.safetensors` |
| VAE | `full_encoder_small_decoder.safetensors` |

### Nodos clave
| Nodo | Función |
|---|---|
| `76` | LoadImage — imagen principal de referencia |
| `81` | LoadImage — segunda imagen de referencia (puede ser igual a 76 si solo hay una) |
| `75` (subgraph) | Pipeline principal con el prompt |

### Procedimiento
```
1. upload_image → subir imagen al input/ de ComfyUI
2. get_workflow → image_flux2_klein_image_edit_9b_base.json
3. modify_workflow → nodo 76: nombre del archivo subido
4. modify_workflow → nodo 81: mismo archivo (o segundo si hay dos refs)
5. modify_workflow → prompt en subgraph 75
6. validate_workflow
7. enqueue_workflow
8. get_history → filename
9. convert_image → view_image
```

### IMPORTANTE
- Con una sola imagen de referencia: poner el mismo archivo en los nodos 76 y 81
- Si el workflow tiene el segundo subgraph (nodo 92) habilitado, desactivarlo si solo se usa una imagen

---

## Wan 2.2 14B — Image to Video

**Archivo:** `video_wan2_2_14B_i2v.json`

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
1. upload_image → imagen al input/ de ComfyUI
2. get_workflow → video_wan2_2_14B_i2v.json
3. modify_workflow → nodo 97: nombre del archivo
4. modify_workflow → nodo 129:93: prompt de movimiento en inglés
5. modify_workflow → nodo 129:98: width y height según tabla de resoluciones
6. validate_workflow
7. enqueue_workflow
8. get_history → esperar resultado (varios minutos)
9. Informar al usuario que el vídeo está en ComfyUI/output/video/
```

### Parámetros clave
| Parámetro | Nodo |
|---|---|
| Imagen de entrada | `97` |
| Prompt positivo (inglés) | `129:93` |
| Width / Height / Frames | `129:98` |
| Frames (patrón 4n+1) | 49 = ~3s, 81 = ~5s a 16fps |

### Notas
- El prompt negativo (nodo `129:89`) está en chino — no tocar
- `length` debe seguir el patrón **4n+1** (49, 81, 121...)
- Output en `ComfyUI/output/video/`

---

## Video Upscale + Interpolación

**Archivo:** `Video-Upscaler-Next-Diffusion.json`

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Upscale | `4x_NMKD-Siax_200k.pth` (fotorrealismo) |
| Interpolación | `rife47.pth` |

### CRÍTICO — NO cargar el JSON guardado para enqueue

El workflow `Video-Upscaler-Next-Diffusion.json` tiene nodos de UI (Labels rgthree, display nodes) y conexiones dinámicas de frame_rate que causan `prompt_outputs_failed_validation` al enqueuar via API. **Construir siempre el workflow mínimo inline:**

```json
{
  "1": {"class_type": "VHS_LoadVideoPath", "inputs": {
    "video": "C:\\Users\\vuski\\Documents\\ComfyUI_windows_portable\\ComfyUI\\output\\video\\FILENAME.mp4",
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

Para framemov, sustituir la ruta de `VHS_LoadVideoPath` por:
`D:\\pinokio\\api\\comfy.git\\ComfyUI\\output\\video\\FILENAME.mp4`

### Valores a sustituir

| Vídeo Wan (entrada) | SCALE_BY | FPS_MULT | OUTPUT_FPS |
|---|---|---|---|
| 270×480 → 1080×1920 | 1.0 | 4 | 64 |
| 480×270 → 1920×1080 | 1.0 | 4 | 64 |
| 270×270 → 1080×1080 | 1.0 | 4 | 64 |

**Nota FPS:** RIFE solo acepta multiplicadores enteros. Desde 16fps base: ×2=32fps, ×4=64fps.

### Pitfalls
- **VHS_LoadVideo NO sirve** — solo lee del input/ folder. Los vídeos de Wan están en output/video/. Usar **VHS_LoadVideoPath** con ruta absoluta Windows completa.
- **VHS_VideoCombine con format video/h264-mp4 requiere campos extra**: `pix_fmt`, `crf`, `save_metadata`, `trim_to_audio`. Sin ellos da 400 Bad Request.
- **frame_rate como referencia dinámica falla** en VHS_VideoCombine via API — hardcodear el valor numérico.
- **audio como referencia dinámica falla** si el mp4 fuente no tiene pista de audio. No conectar el campo audio.

---

## Procedimiento estándar (txt2img)

```
1. get_workflow → nombre.json  ← SIEMPRE usar el JSON guardado
2. modify_workflow → prompt, seed, resolución
3. validate_workflow
4. enqueue_workflow
5. get_history → filename
6. convert_image (jpeg, 75) → view_image
```

**CRÍTICO:** Nunca construir el workflow desde cero — siempre cargar el JSON guardado. Excepción: Video-Upscaler-Next-Diffusion.json (ver sección arriba).
