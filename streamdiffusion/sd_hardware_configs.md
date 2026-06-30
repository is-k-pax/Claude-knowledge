# SD Configuraciones Hardware

## VRAM Budget Reference (datos oficiales RTX 4090 / 24GB)

nvidia-smi incluye ~5 GB de baseline Windows.

| Config | VRAM | FPS | Notas |
|---|---|---|---|
| Base SDXL-turbo TRT (512x512) | ~18 GB | ~26 | Baseline SDXL |
| + Single ControlNet (canny) | ~18 GB | ~15 | +2.4 GB por engine CN TRT |
| + Depth preprocessor (CPU) | ~25 GB | ~9 | PyTorch depth añade ~5 GB |
| + Depth preprocessor (depth_tensorrt) | ~18 GB | ~14.5 | Engine TRT ~52 MB, auto-build |
| + Dual CN (depth_tensorrt + canny) | ~23.5 GB | 4-9 | Al límite en 4090 |
| + IP Adapter | +4.3 GB | ~19 | Sobre la config base |
| + StreamV2V (cached attention) | ~13 GB | ~21 | Requiere peft |

---

## PC Torre — RTX 4090 24GB VRAM, 128GB RAM

### Configuración recomendada: MÁXIMA
Esta GPU puede con prácticamente todo.

**Config base recomendada:**
- Modelo: sdxl-turbo (calidad máxima)
- Aceleración: TensorRT
- Resolución: 512x512 (estándar) o hasta 768x768
- Steps: 1-2

**Features que puedes activar simultáneamente:**
| Combo | VRAM estimado | FPS estimado | ¿Viable? |
|---|---|---|---|
| SDXL + single CN (depth_trt) | ~18 GB | ~14.5 | SÍ — config ideal |
| SDXL + single CN + IP Adapter | ~22 GB | ~12 | SÍ — al límite pero funciona |
| SDXL + dual CN (depth_trt + canny) | ~23.5 GB | 4-9 | POSIBLE pero al límite |
| SDXL + single CN + StreamV2V | ~18 GB | ~12 | SÍ |
| SDXL + single CN + V2V + IP Adapter | ~22+ GB | ~8 | LÍMITE, probar |
| SDXL + dual CN + IP Adapter | >24 GB | — | NO — excede VRAM |

**Config "segura" para performance:**
- sdxl-turbo + single ControlNet (depth_tensorrt) + 512x512
- ~18 GB VRAM, ~14.5 FPS
- Añadir IP Adapter si necesitas style transfer (+4.3 GB)

**Config "máxima calidad":**
- sdxl-turbo + single CN (depth_trt) + StreamV2V + 512x512
- ~18 GB, buena consistencia temporal

---

## PC Portátil — RTX 5080 16GB VRAM, 32GB RAM

### Configuración recomendada: CONSERVADORA
16GB de VRAM limita las combinaciones posibles.

**IMPORTANTE sobre RTX 50-series:**
- CUDA 12.8 es OBLIGATORIO
- Puede necesitar múltiples intentos de instalación
- TensorRT puede tardar más en builds
- Si hay problemas, probar v0.2.99

**Config base recomendada:**
- Modelo: sd-turbo (ahorra VRAM, ~8 GB base) O sdxl-turbo (si cabe)
- Aceleración: TensorRT
- Resolución: 512x512 (NO subir)
- Steps: 1

**Opciones con sd-turbo (~8 GB base):**
| Combo | VRAM estimado | ¿Viable? |
|---|---|---|
| sd-turbo solo | ~8 GB | SÍ — holgado |
| sd-turbo + single CN | ~10 GB | SÍ |
| sd-turbo + single CN + StreamV2V | ~12 GB | SÍ |
| sd-turbo + IP Adapter | NO | NO — sd-turbo es SD 2.1, IP Adapter incompatible |

**Opciones con sdxl-turbo (~13 GB con V2V, ~18 GB base TRT):**
| Combo | VRAM estimado | ¿Viable? |
|---|---|---|
| sdxl-turbo base TRT | ~18 GB | NO — excede 16 GB |

CONCLUSIÓN 5080: Usar sd-turbo como modelo base. SDXL probablemente no cabe con TRT.

**Alternativa si SDXL es necesario:**
- Probar sin TensorRT (aceleración = xformers o none)
- Pero: sin TRT no hay ControlNet, IP Adapter ni StreamV2V
- FPS será bajo

**Config recomendada portátil:**
- sd-turbo + TensorRT + single ControlNet (canny o depth_trt) + 512x512
- ~10-12 GB VRAM, deja margen
- NO IP Adapter (incompatible con sd-turbo)
- StreamV2V opcional si queda VRAM

---

## Notas generales

- Cerrar otras aplicaciones GPU-intensivas antes de usar SD
- limitfps (Settings 2) para controlar carga GPU — útil en portátil para temperatura
- Unload Models pulse libera VRAM entre sesiones
- Si FPS degrada con el tiempo: restart stream
- Benchmark button (About page) copia info de rendimiento al clipboard
