# SD Compatibilidad de Modelos (v0.3.1)

## Modelos base disponibles

| Modelo | Arquitectura | VRAM base (TRT) | Notas |
|---|---|---|---|
| stabilityai/sd-turbo | SD 2.1 | ~8 GB | Más ligero. NO compatible con IP Adapter ni LoRA SD1.5 |
| stabilityai/sdxl-turbo | SDXL | ~18 GB | Mayor calidad. Necesita ~24GB para todas las features |
| prompthero/openjourney-v4 | SD 1.5 | ~8 GB | Estilo alternativo |
| Modelos SD 1.5 custom (HF) | SD 1.5 | ~8 GB | Compatible con LoRA SD1.5 e IP Adapter |
| Modelos SDXL custom (HF) | SDXL | ~18 GB | Compatible con LoRA SDXL e IP Adapter |

## Matriz de compatibilidad cruzada

### ControlNet por arquitectura

| ControlNet | SD 1.5 | SD 2.1 (sd-turbo) | SDXL |
|---|---|---|---|
| xinsir/controlnet-depth-sdxl-1.0 | NO | NO | SÍ |
| xinsir/controlnet-canny-sdxl-1.0 | NO | NO | SÍ |
| xinsir/controlnet-tile-sdxl-1.0 | NO | NO | SÍ |
| ControlNets SD 1.5 genéricos | SÍ | NO | NO |

REGLA: el ControlNet DEBE coincidir con la arquitectura del modelo base.

### IP Adapter por arquitectura

| Feature | SD 1.5 | SD 2.1 (sd-turbo) | SDXL |
|---|---|---|---|
| IP Adapter | SÍ | NO | SÍ |
| IP Adapter FaceID | SÍ | NO | SÍ |

REGLA: IP Adapter NO funciona con sd-turbo (arquitectura SD 2.1).
Requiere insightface (se instala automáticamente).
Debe activarse ANTES de start stream. No se puede toggle después.

### LoRA por arquitectura

| LoRA tipo | SD 1.5 | SD 2.1 (sd-turbo) | SDXL |
|---|---|---|---|
| LoRA SD 1.5 | SÍ | NO | NO |
| LoRA SD 2.1 | NO | SÍ (raros) | NO |
| LoRA SDXL | NO | NO | SÍ |

AVISO: LoRA en v0.3.1 es experimental/no testeado. v0.2.99 tiene soporte confirmado.

### Aceleración y features

| Feature | Sin aceleración | xformers | TensorRT |
|---|---|---|---|
| Generación básica | SÍ | SÍ | SÍ |
| ControlNet | NO | NO | SÍ (obligatorio) |
| IP Adapter | NO | NO | SÍ (obligatorio) |
| StreamV2V / Cached Attention | NO | NO | SÍ (obligatorio) |
| Resolución flexible 384-1024 | SÍ | SÍ | SÍ |
| Step count flexible | SÍ | SÍ | SÍ |

REGLA: TensorRT es OBLIGATORIO para ControlNet, IP Adapter y StreamV2V.

### StreamV2V / Cached Attention requisitos

| Requisito | Valor |
|---|---|
| Aceleración | TensorRT (obligatorio) |
| Scheduler | TCD (obligatorio, no LCM) |
| Resolución | Locked al build del engine |
| peft package | Obligatorio (se instala con sd_installer) |
| Modo | img2img recomendado |

## Step Schedule (T-Index) por modelo

| Modelo / Caso | Steps recomendados | Rango T-Index | Notas |
|---|---|---|---|
| sd-turbo / sdxl-turbo txt2img | 1 | 35-45 | 1 step es suficiente para turbo |
| sd-turbo / sdxl-turbo img2img | 1-2 | 35-45 (más alto = más fiel al input) | |
| Con ControlNet | 1-2 | 30-40 | Más steps = más adherencia al control |
| Con StreamV2V | 1-2 | 35-45 | |
| Modelos no-turbo | 2-4 | 20-35 | Necesitan más steps |

NOTA: Steps se pueden cambiar sin rebuild de TensorRT.
T-Index más alto (40-49) = más cercano al input. Más bajo (1-20) = más transformación AI.

## Schedulers y Samplers

| Scheduler | Cuándo usar |
|---|---|
| lcm | Default. Para uso general sin StreamV2V |
| tcd | OBLIGATORIO para StreamV2V / cached attention |

| Sampler | Notas |
|---|---|
| simple | Default, funciona bien con todo |
| sgm uniform | Alternativa |
| normal / ddim / beta / karras | Otras opciones disponibles |

## VAE

| VAE | Arquitectura | Notas |
|---|---|---|
| auto | — | Selecciona automáticamente según modelo |
| madebyollin/taesd | SD 1.5 / SD 2.1 | Tiny AutoEncoder, más rápido |
| madebyollin/taesdxl | SDXL | Tiny AutoEncoder para SDXL |
| stabilityai/sd-vae-ft-mse | SD 1.5 | VAE de alta calidad para SD 1.5 |

## TensorRT Engine — qué desencadena rebuild

| Cambio | ¿Rebuild? |
|---|---|
| Cambiar modelo | SÍ |
| Toggle ControlNet on/off | SÍ |
| Toggle IP Adapter on/off | SÍ |
| Cambiar resolución (384-1024) | NO |
| Cambiar step count | NO |
| Cambiar prompt | NO |
| Cambiar seed | NO |

EXCEPCIÓN: Engines de StreamV2V están locked a la resolución del build.

## Guardar y cargar engines TRT

Ubicación: StreamDiffusion/engines/td/
- Los engines se cachean automáticamente tras primer build
- Builds posteriores cargan en <30 segundos
- Para forzar rebuild: borrar la carpeta engines/td/
- Los engines son específicos de la GPU (no transferibles entre GPUs diferentes)
- Un engine válido pesa 1-8 GB según modelo y features habilitadas

## Modelos que funcionan (Working Models)

Tras 200+ frames generados con éxito, el modelo se guarda en:
StreamDiffusion/streamdiffusionTD/working_models.json
Aparece en el dropdown "My Models" del operador.
