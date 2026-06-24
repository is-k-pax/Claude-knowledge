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

### Parámetros clave
| Parámetro | Valor por defecto | Nodo |
|---|---|---|
| Resolución | 640x640 | `129:98` (width/height) |
| Frames | 81 | `129:98` (length) |
| FPS | 16 | `129:94` |
| Steps (normal) | 20 | `129:128` |
| Steps (4step LoRA) | 4 | `129:118` |
| CFG (normal) | 3.5 | `129:126` |
| CFG (4step LoRA) | 1 | `129:122` |
| Activar 4step LoRA | true/false | `129:131` |
| Imagen de entrada | nombre del archivo | nodo `97` |

### Qué cambiar para cada generación
1. **Prompt positivo** — nodo `129:93`, en inglés, describir el movimiento deseado
2. **Imagen de entrada** — nodo `97`, campo `image`: nombre del archivo en la carpeta `input/`
3. **Activar LoRA de 4 pasos** — nodo `129:131`: `true` = rápido (4 steps), `false` = calidad (20 steps)
4. **Resolución** — nodo `129:98`: width y height (múltiplos de 16)

### Notas
- El prompt negativo ya está en chino (el modelo es chino, funciona mejor así) — no tocar
- Con 4step LoRA activo: generación muy rápida pero menor detalle
- Output en `output/video/Wan2.2_i2v_*.mp4` → acceder via carpeta compartida
- La imagen de entrada debe subirse primero con `upload_image`

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
| Sampler | euler | `92:101` |
| Scheduler | Flux2Scheduler | `92:102` |
| Imagen 1 | nombre del archivo | nodo `76` |
| Imagen 2 | nombre del archivo | nodo `81` |
| Resolución | auto (1MP desde imagen 1) | `92:111` |

### Qué cambiar para cada generación
1. **Prompt** — nodo `92:109`: describir qué hacer con la imagen
2. **Imagen de entrada** — nodo `76` Y nodo `81`: ambos con el mismo archivo si solo hay una imagen
3. **Seed** — nodo `92:106` para reproducibilidad

### IMPORTANTE — uso con una sola imagen
El workflow tiene dos nodos LoadImage (76 y 81) porque fue diseñado para mezclar dos referencias.
**Con una sola imagen: poner el mismo archivo en los dos nodos (76 y 81).**
Los nodos `92:85` y `92:111` (ImageScaleToTotalPixels) deben apuntar ambos al mismo LoadImage.
`ReferenceLatent` usa la imagen como referencia de estructura — funciona perfectamente con una sola imagen repetida.

### Notas
- CFG=1 y steps=4 son óptimos para este modelo — no subir
- El CLIP es Qwen 3 4B — entiende prompts largos y detallados en inglés
- La imagen debe subirse con `upload_image` antes de ejecutar
- Output en `output/Flux2-Klein_*.png` → guardar en `%USERPROFILE%\Documents\comfyUI-Claude-output\`
- NO usar `ae.safetensors` como VAE — el nombre correcto es `flux2-vae.safetensors`
- NO cambiar el modelo por Flux 1 ni Kontext si falla — revisar primero que el VAE y CLIP sean los correctos

---

## Procedimiento estándar

```
1. Subir imagen:          upload_image
2. Cargar workflow:       get_workflow → nombre.json  ← SIEMPRE usar el JSON guardado
3. Modificar parámetros:  modify_workflow → prompt, imagen (nodos 76 Y 81), seed
4. Validar:               validate_workflow
5. Ejecutar:              enqueue_workflow
6. Esperar resultado:     get_history → filename
7. Descargar:             get_image → filename
8. Guardar:               %USERPROFILE%\Documents\comfyUI-Claude-output\ (crear si no existe)
9. Confirmar al usuario la ruta exacta donde quedó guardada
```

**CRÍTICO:** Siempre cargar el JSON con `get_workflow` — nunca construir el workflow desde cero.
Los nombres de modelos, VAE y CLIP están en el JSON y son los correctos para este sistema.
