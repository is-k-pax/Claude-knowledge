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

**Por qué:** El chat normal de Claude Desktop no puede ejecutar comandos locales (SCP). Cowork con "Uso de computadora" activado sí puede ejecutar SCP automáticamente para copiar la imagen al PC de ComfyUI.

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
5. validate_workflow
6. enqueue_workflow
7. get_history → esperar resultado (varios minutos)
8. Decir al usuario que el vídeo está en \\100.102.173.86\comfyui-output\video\
```

### Parámetros clave
| Parámetro | Nodo |
|---|---|
| Imagen de entrada | nodo `97` |
| Prompt positivo (inglés) | nodo `93` |
| Frames (81 = ~5s a 16fps) | nodo `98` |

### Notas
- El prompt negativo (nodo `89`) está vacío — no tocar
- Output en `output/video/` → acceder via `\\100.102.173.86\comfyui-output`

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
