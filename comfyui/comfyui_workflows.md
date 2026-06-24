# ComfyUI — Workflows

Workflows probados y listos para usar. Los JSONs están guardados en:
`D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\`

Para ejecutar un workflow: cargar con `get_workflow`, ajustar parámetros, ejecutar con `enqueue_workflow`.

**Última revisión:** junio 2026.

---

## Cómo subir imágenes a ComfyUI desde el PC de casa

**CRÍTICO:** El MCP de ComfyUI no puede leer rutas Linux (`/mnt/user-data/uploads/`) ni rutas de usuario de Windows. La única forma de subir imágenes desde el PC de casa es via SCP sobre Tailscale.

### Procedimiento para subir imagen via SCP
```powershell
# Desde PowerShell del PC de casa:
scp -i "$env:USERPROFILE\.ssh\comfyui_key" "<ruta_imagen_local>" "framemov@100.102.173.86:D:/pinokio/api/comfy.git/ComfyUI/input/<nombre_archivo>"
```

Una vez copiada, usar el nombre del archivo en el nodo LoadImage del workflow.

### Cuando el usuario adjunta una imagen en el chat
1. Guardar la imagen en el PC de casa (la ruta aparece en el contexto de la sesión)
2. Ejecutar SCP para copiarla al input de ComfyUI en `framemov@100.102.173.86`
3. Usar el nombre del archivo en el workflow

---

## Cómo entregar el resultado al usuario

### Imágenes
```
1. get_history → obtener el filename del output
2. get_image (filename) → descarga la imagen
3. Presentar inline en el chat
```

**NOTA:** Windows bloquea escritura en `Documents` desde Cowork/Dispatch. No intentar guardar ahí — fallará. Las imágenes quedan en la carpeta de outputs de la sesión (icono de carpeta en Dispatch).

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
**Uso:** Generar imágenes desde texto. Basado en el template oficial de ComfyUI (Flux.2 Klein 9B) adaptado al modelo 4B disponible.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-4b-fp8.safetensors` |
| VAE | `flux2-vae.safetensors` |
| CLIP | `qwen_3_4b.safetensors` |

### Parámetros clave
| Parámetro | Valor | Nodo |
|---|---|---|
| Steps | 20 | `75:62` |
| CFG | 5 | `75:63` |
| Sampler | euler | `75:61` |
| Scheduler | Flux2Scheduler | `75:62` |
| Resolución | 1024x1024 | `75:68` / `75:69` |
| Prompt | texto | nodo `76` |

### Qué cambiar para cada generación
1. **Prompt** — nodo `76`, campo `value`
2. **Resolución** — nodos `75:68` (width) y `75:69` (height)
3. **Seed** — nodo `75:73`, campo `noise_seed`

### Notas
- Más rápido que Flux 1 Dev (30s vs 42s) y mejor estilo fotográfico
- Output en `output/Flux2-Klein_*.png`

---

## Flux 1 Dev — Text to Image (clásico)

**Archivo:** `flux1_dev_txt2img.json`
**Uso:** Generar imágenes desde texto con Flux 1 Dev.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Checkpoint | `flux1-dev-fp8.safetensors` (en `checkpoints/`) |

### Notas
- Usa CheckpointLoaderSimple — solo ve modelos en `checkpoints/`, no en `diffusion_models/`
- Output en `output/Flux1-Dev_*.png`

---

## Flux 2 Klein — Img2Img con referencia

**Archivo:** `flux2_klein_img2img_editing.json`
**Uso:** Editar una imagen usando Flux 2 Klein como modelo de edición con referencia.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-4b-fp8.safetensors` |
| VAE | `flux2-vae.safetensors` ← nombre exacto, no usar `ae.safetensors` |
| CLIP | `qwen_3_4b.safetensors` |

### Parámetros clave
| Parámetro | Valor por defecto | Nodo |
|---|---|---|
| Steps | 4 | `92:102` |
| CFG | 1 | `92:103` |
| Imagen 1 | nombre del archivo | nodo `76` |
| Imagen 2 | nombre del archivo | nodo `81` |

### IMPORTANTE — uso con una sola imagen
Con una sola imagen: poner el mismo archivo en los dos nodos (76 y 81).
NO usar `ae.safetensors` como VAE — el nombre correcto es `flux2-vae.safetensors`.
NO cambiar el modelo por Flux 1 ni Kontext si falla.

### Subir imagen de entrada
Usar el procedimiento SCP descrito arriba antes de ejecutar el workflow.

---

## Wan 2.2 14B — Image to Video

**Archivo:** `video_wan2_2_14B_i2v.json`
**Uso:** Animar una imagen fija generando un vídeo a partir de ella. ~5 segundos a 16fps.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet (low noise) | `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` |
| UNet (high noise) | `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` |
| VAE | `wan_2.1_vae.safetensors` |
| CLIP | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` |
| LoRA low noise | `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors` |
| LoRA high noise | `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` |

### Procedimiento completo con imagen desde el PC de casa
```
1. Guardar imagen adjunta en el PC de casa
2. SCP → copiar a framemov@100.102.173.86:D:/pinokio/api/comfy.git/ComfyUI/input/<nombre>.png
3. get_workflow → video_wan2_2_14B_i2v.json
4. modify_workflow → nodo 97, imagen: <nombre>.png
5. modify_workflow → nodo 93, prompt de movimiento en inglés
6. validate_workflow
7. enqueue_workflow
8. get_history → esperar resultado (puede tardar varios minutos)
9. Decir al usuario que el vídeo está en \\100.102.173.86\comfyui-output\video\
```

### Parámetros clave
| Parámetro | Valor | Nodo |
|---|---|---|
| Imagen de entrada | nombre del archivo | nodo `97` |
| Prompt positivo | texto en inglés | nodo `93` |
| Resolución | 1024x768 | nodo `98` |
| Frames | 81 (~5s a 16fps) | nodo `98` |

### Notas
- El prompt negativo (nodo `89`) ya está vacío — no tocar
- Con LoRA 4steps activo: 4 steps, muy rápido
- Output en `output/video/` → acceder via `\\100.102.173.86\comfyui-output`

---

## Procedimiento estándar (imágenes txt2img — sin imagen de entrada)

```
1. Cargar workflow:        get_workflow → nombre.json  ← SIEMPRE usar el JSON guardado
2. Modificar parámetros:  modify_workflow → prompt, seed
3. Validar:               validate_workflow
4. Ejecutar:              enqueue_workflow
5. Esperar resultado:     get_history → filename
6. Presentar:             get_image → inline en el chat
```

**CRÍTICO:** Siempre cargar el JSON con `get_workflow` — nunca construir el workflow desde cero.
