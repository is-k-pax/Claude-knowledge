# ComfyUI — Workflows

Workflows probados y listos para usar. Los JSONs están guardados en:
`D:\pinokio\api\comfy.git\ComfyUI\user\default\workflows\`

Para ejecutar un workflow: cargar con `get_workflow`, ajustar parámetros, ejecutar con `enqueue_workflow`.

**Última revisión:** junio 2026.

---

## Cómo entregar el resultado al usuario

### Imágenes → guardar en carpeta local + get_image
Después de `enqueue_workflow`, siempre hacer:
```
1. get_history → obtener el filename del output
2. get_image (filename) → descarga la imagen
3. Guardar en la carpeta de outputs del usuario (ver abajo)
4. Confirmar al usuario la ruta donde está guardada
```

### Carpeta de outputs del usuario (universal)
Siempre guardar los resultados aquí:
```
%USERPROFILE%\Documents\comfyUI-Claude-output\
```

En Python/código esto se resuelve como:
```python
import os
output_dir = os.path.join(os.path.expanduser("~"), "Documents", "comfyUI-Claude-output")
os.makedirs(output_dir, exist_ok=True)
```

Esta ruta funciona en cualquier PC independientemente del nombre de usuario.
Si la carpeta no existe, crearla antes de guardar.

### Vídeos → carpeta compartida + carpeta local
Los vídeos pesan 20-50MB. Se guardan automáticamente en el PC de ComfyUI en:
`D:\pinokio\api\comfy.git\ComfyUI\output\video\`

Esta carpeta está compartida en red via Tailscale como `\\100.102.173.86\comfyui-output`.
El usuario puede acceder desde el PC de casa abriendo esa ruta en el explorador de Windows.

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
- Basado en el template oficial de ComfyUI `image_flux2_text_to_image_9b.json` con modelos 9B → 4B
- Más rápido que Flux 1 Dev (30s vs 42s) y mejor estilo fotográfico
- Output en `output/Flux2-Klein_*.png` → guardar en `%USERPROFILE%\Documents\comfyUI-Claude-output\`

---

## Flux 1 Dev — Text to Image (clásico)

**Archivo:** `flux1_dev_txt2img.json`
**Uso:** Generar imágenes desde texto con Flux 1 Dev. Workflow estándar con CheckpointLoader.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| Checkpoint | `flux1-dev-fp8.safetensors` (en `checkpoints/`) |

### Parámetros clave
| Parámetro | Valor | Nodo |
|---|---|---|
| Steps | 20 | nodo `5` |
| CFG | 1 | nodo `5` |
| Sampler | euler | nodo `5` |
| Scheduler | simple | nodo `5` |
| Resolución | 1024x1024 | nodo `4` |

### Notas
- Usa CheckpointLoaderSimple — solo ve modelos en `checkpoints/`, no en `diffusion_models/`
- Más lento que Flux 2 Klein 4B pero resultados también muy buenos
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

### Qué cambiar para cada generación
1. **Prompt positivo** — nodo `129:93`, en inglés, describir el movimiento
2. **Imagen de entrada** — nodo `97`, campo `image`
3. **Activar LoRA de 4 pasos** — nodo `129:131`: `true` = rápido, `false` = calidad

### Notas
- El prompt negativo ya está en chino — no tocar
- Output en `output/video/` → acceder via carpeta compartida `\\100.102.173.86\comfyui-output`

---

## Procedimiento estándar

```
1. Cargar workflow:        get_workflow → nombre.json  ← SIEMPRE usar el JSON guardado
2. Modificar parámetros:  modify_workflow → prompt, imagen, seed
3. Validar:               validate_workflow
4. Ejecutar:              enqueue_workflow
5. Esperar resultado:     get_history → filename
6. Descargar:             get_image → filename
7. Guardar:               %USERPROFILE%\Documents\comfyUI-Claude-output\ (crear si no existe)
8. Confirmar al usuario la ruta exacta
```

**CRÍTICO:** Siempre cargar el JSON con `get_workflow` — nunca construir el workflow desde cero.
Los nombres de modelos, VAE y CLIP están en el JSON y son los correctos para este sistema.
