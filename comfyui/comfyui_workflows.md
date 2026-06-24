# ComfyUI — Workflows

Workflows probados y listos para usar. Los JSONs están guardados en:
`D:\pinokio\api\comfy.git\ComfyUI\user\workflows\`

Para ejecutar un workflow: cargar con `get_workflow`, ajustar parámetros, ejecutar con `enqueue_workflow`.

**Última revisión:** junio 2026.

---

## Cómo entregar el resultado al usuario

### Imágenes → get_image (inline en el chat)
Después de `enqueue_workflow`, siempre hacer:
```
1. get_history → obtener el filename del output
2. get_image (filename) → devuelve la imagen inline en el chat
```
Nunca dejar el flujo sin llamar a `get_image` al final. El usuario debe ver la imagen en el chat.

### Vídeos → carpeta compartida
Los vídeos pesan 20-50MB — no se pueden enviar inline. Se guardan automáticamente en:
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

## Flux 2 Klein — Img2Img con dos referencias

**Archivo:** `flux2_klein_img2img_editing.json`
**Uso:** Editar o mezclar dos imágenes usando Flux 2 Klein como modelo de edición.

### Modelos necesarios
| Tipo | Archivo |
|---|---|
| UNet | `flux-2-klein-4b-fp8.safetensors` |
| VAE | `flux2-vae.safetensors` |
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
1. **Prompt** — nodo `92:109`: describir qué hacer con las dos imágenes
2. **Imagen 1** — nodo `76`, campo `image`: primera referencia (estilos, colores, texturas)
3. **Imagen 2** — nodo `81`, campo `image`: segunda referencia (estructura, composición)
4. **Seed** — nodo `92:106` para reproducibilidad

### Cómo funciona
Usa `ReferenceLatent` para codificar ambas imágenes como conditioning. La imagen 1 actúa como referencia de estilo/color, la imagen 2 como referencia de contenido/estructura. El prompt describe cómo combinarlas.

### Notas
- CFG=1 y steps=4 son óptimos para este modelo — no subir
- El CLIP es Qwen 3 4B — entiende prompts largos y detallados en inglés
- Ambas imágenes deben subirse con `upload_image` antes de ejecutar
- Output en `output/Flux2-Klein_*.png` → entregar con `get_image` inline en el chat

---

## Procedimiento estándar

```
1. Subir imágenes:        upload_image
2. Cargar workflow:       get_workflow → nombre.json
3. Modificar parámetros:  modify_workflow → prompt, imagen, seed
4. Validar:               validate_workflow
5. Ejecutar:              enqueue_workflow
6. Esperar resultado:     get_history → filename
7. Entregar:              get_image → inline en chat (imágenes)
                          carpeta compartida (vídeos)
```
