# SD Features Guide (v0.3.1)

## ControlNet — qué hace cada tipo

### Tipos de ControlNet disponibles (SDXL)
| ControlNet | Para qué sirve | Cuándo usarlo |
|---|---|---|
| depth (xinsir/controlnet-depth-sdxl-1.0) | Mantiene la estructura 3D/profundidad de la escena | Webcam, escenas con personas, objetos 3D, mantener composición espacial |
| canny (xinsir/controlnet-canny-sdxl-1.0) | Mantiene los bordes/siluetas del input | Dibujos, líneas definidas, mantener formas exactas |
| tile (xinsir/controlnet-tile-sdxl-1.0) | Mantiene detalles y texturas del input | Upscaling, preservar textura, img2img con alta fidelidad |

### Preprocessors
| Preprocessor | Cómo funciona | Performance |
|---|---|---|
| depth | Estimación de profundidad por CPU | +5 GB VRAM, lento |
| depth_tensorrt | Estimación de profundidad por GPU (TRT) | ~52 MB, 60% más rápido que CPU, auto-build en primer uso (~2 min) |
| canny | Detección de bordes | Rápido, bajo coste |
| hed | Detección de bordes holística | Similar a canny pero más suave |
| external | Input ya preprocesado (tú envías el depth/canny map) | Sin coste extra |
| feedback | Usa el output anterior como conditioning | Efectos feedback interesantes |

RECOMENDACIÓN: Siempre usar depth_tensorrt en vez de depth. Misma calidad, 60% más rápido, fracción del VRAM.

### ¿Cuándo usar ControlNet?
- Cuando quieres que el output mantenga la ESTRUCTURA del input (composición, silueta, profundidad)
- En performances con webcam: depth para mantener la silueta de la persona
- En img2img donde quieres más control que solo el T-Index

### ¿Cuándo usar más de un ControlNet?
- Combinación verificada: depth_tensorrt + canny (estructura + bordes)
- PERO: en 24GB GPU ocupa ~23.5 GB y baja a 4-9 FPS
- RECOMENDACIÓN: single ControlNet para la mayoría de workflows
- Dual ControlNet solo si tienes VRAM de sobra y necesitas precisión extrema

---

## StreamV2V / Cached Attention

### Qué es
Sistema de consistencia temporal entre frames. Cachea mapas de atención de frames anteriores y los reutiliza, suavizando las transiciones frame-a-frame. El resultado es un video más coherente y menos flickering.

### Cómo funciona
- Mantiene un buffer circular de N frames (configurable con Max Frames)
- Cada N intervals, actualiza el cache con el frame actual
- Los mapas de atención cached influyen en la generación del frame siguiente

### Parámetros clave
| Parámetro | Default | Efecto |
|---|---|---|
| Max Frames | 3 | Más frames = más consistencia temporal, más VRAM |
| Interval | 1 | Cada cuántos frames actualiza el cache. Más bajo = actualizaciones más frecuentes |

### Requisitos
- TensorRT: OBLIGATORIO
- Scheduler: TCD (no LCM)
- Resolución: LOCKED al build del engine (si cambias resolución, rebuild)
- peft package: necesario

### ¿Cuándo usar StreamV2V?
- Video input (webcam, video files) donde quieres consistencia temporal
- Performances donde el flickering entre frames es molesto
- NO lo uses si quieres variación frame-a-frame (arte generativo con chaos)

### ¿Es compatible con TensorRT?
SÍ, de hecho es OBLIGATORIO. Sin TRT, StreamV2V no funciona (paths sin TRT están rotos).

### ¿Es recomendable combinarlo con ControlNet?
- SÍ se puede combinar (StreamV2V + ControlNet)
- Pero el VRAM se suma: vigila el budget
- En la práctica, ControlNet ya da bastante estabilidad estructural, así que V2V añade sobre todo suavidad temporal

---

## ControlNet vs StreamV2V — cuándo usar cada uno

| Quiero... | Usar |
|---|---|
| Mantener la estructura/silueta del input | ControlNet |
| Suavizar transiciones entre frames (anti-flicker) | StreamV2V |
| Ambas cosas | ControlNet + StreamV2V (vigilar VRAM) |
| Máxima libertad creativa, chaos generativo | Ninguno de los dos |
| Webcam con persona reconocible | ControlNet depth |
| Video input con movimiento suave | StreamV2V |
| Video input con estructura preservada Y suavidad | ControlNet + StreamV2V |

---

## IP Adapter

### Qué es
Permite usar una imagen de referencia como "prompt visual". En vez de describir con texto lo que quieres, le muestras una imagen y el modelo genera algo con estilo/contenido similar.

### Para qué sirve
- Transferir estilo de una imagen de referencia
- Mantener coherencia visual con una referencia
- FaceID: preservar rasgos faciales de una persona

### Compatibilidades
| Modelo base | IP Adapter | FaceID |
|---|---|---|
| SD 1.5 | SÍ | SÍ |
| sd-turbo (SD 2.1) | NO | NO |
| SDXL / sdxl-turbo | SÍ | SÍ |

### Requisitos
- TensorRT: OBLIGATORIO
- Debe activarse ANTES de start stream (no se puede toggle después)
- FaceID necesita insightface + modelo buffalo_l (se instalan automáticamente)
- Coste VRAM: +4.3 GB

### ¿Es compatible con ControlNet?
SÍ, se pueden combinar. IP Adapter da el estilo, ControlNet da la estructura.
Pero suma VRAM: verifica en sd_hardware_configs.md.

### ¿Es compatible con StreamV2V?
SÍ, se pueden combinar, pero la suma de VRAM puede ser problemática en GPUs <24GB.

---

## FX Processors

### Qué son
Hooks de procesamiento en 4 etapas del pipeline de difusión. Permiten modificar la imagen o el latent antes/después de la difusión.

### Procesadores built-in
| Procesador | Etapa | Para qué |
|---|---|---|
| feedback_loop | image_pre | Zoom, pan, rotación estilo Deforum. Efecto se acumula cada frame |
| feedback_grade | image_pre | Color grading que se acumula (brillo, contraste, saturación, hue, temperatura) |

### Combo recomendado
feedback_loop (zoom: 1.02, strength: 0.7) + feedback_grade (strength: 0.5, hue_degrees: 2)
= Infinite zoom con color cycling. Valores pequeños porque todo se acumula.

### Notas
- Solo disponible en backend Local (no Daydream Cloud)
- Se pueden crear procesadores custom en custom_processors/
- Los parámetros se actualizan en vivo por OSC sin restart
- Cambios en el código del procesador SÍ requieren stop/start del stream
