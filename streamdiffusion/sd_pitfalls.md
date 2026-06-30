# SD Pitfalls & Troubleshooting (v0.3.1)

## Herramienta de diagnóstico integrada

Siempre como primer paso, activar el venv desde la página Install y ejecutar:
  python -m sd_installer verify    # 13 checks del entorno
  python -m sd_installer repair    # auto-fix de dependencias
  python -m sd_installer diagnose  # dump completo para bug reports

---

## Instalación

### Python no encontrado
Síntoma: "Python not found" o instalación falla.
Fix: Instalar Python 3.11.9 (python.org). Marcar "Add to PATH". Restart TD.
IMPORTANTE: Python 3.12 y 3.13 NO están soportados.

### Error "cudart" import (RTX 50-series)
Síntoma: cannot import name 'cudart' from 'cuda'.
Causa: CUDA 12.8 necesario para RTX 50-series.
Fix: Verificar versión de CUDA toolkit. Consultar Discord.

### "polygraphy" module missing
Síntoma: ModuleNotFoundError: No module named 'polygraphy'.
Fix: Click "Install TensorRT" en la página Install del operador.

### Conflicto de nombre de carpeta
Síntoma: Import failed: no module named 'streamdiffusion.config'.
Fix: NO nombrar la carpeta de instalación "streamdiffusion". Usar "StreamDiff031" o similar.

### flash-attn crash
Síntoma: Pipeline crash al importar con errores de flash-attn.
Fix: pip uninstall flash-attn

### Scripts fix v0.3.0 rompen v0.3.1
Síntoma: Features rotas tras ejecutar Fix_All_Dependencies.bat de v0.3.0.
Causa: Sobreescribe el fork de diffusers (varshith15) con vanilla.
Fix: python -m sd_installer repair

### Conflictos entre versiones
REGLA: v0.3.1 DEBE instalarse en carpeta SEPARADA de v0.2.99 y v0.3.0.

---

## Runtime

### "Acceleration has failed"
Fix: 1) Borrar engines/td/ 2) IP Adapter OFF si usas sd-turbo 3) Restart stream.

### FPS degrada con el tiempo
Fix: Restart stream periódicamente. Restart TD si persiste.

### CUDA out of memory
Ver sd_hardware_configs.md para VRAM budget de tu GPU.
Fixes rápidos: Unload Models pulse, bajar resolución, single CN, depth_trt en vez de depth CPU.

### TD crash al Start Stream
Fix: Verificar numpy, verificar CUDA, probar sin TensorRT primero.

### Frames negros
Causas: prompt weights sumando 0, IP Adapter con sd-turbo, error stale de sesión anterior.

---

## TensorRT Engines

### Engine corrupto o mal hecho
Cómo identificar un engine malo:
- Crash al cargar o "Acceleration has failed"
- Se creó con config diferente a la actual
- FPS anormalmente bajo o artifacts visuales

Cómo verificar:
- Engine válido: 1-8 GB, carga en <30s (tras primer build)
- Primer build: 20-30+ min es NORMAL, no interrumpir

Fix universal: Borrar toda la carpeta engines/td/ y rebuild.

### Cuándo se puede borrar un engine
- Si cambias de modelo → el engine anterior es inútil, borrar
- Si cambias ControlNet on/off → engine anterior inútil
- Si cambias IP Adapter on/off → engine anterior inútil
- Engines pesan 1-8 GB cada uno, borrar los obsoletos libera espacio

### depth_tensorrt build
- Auto-build en primer uso (~2 min en 4090)
- Si falla: verificar versión de onnx con sd_installer verify

---

## Dependencias críticas (version pins v0.3.1)

| Package | Requisito | Por qué |
|---|---|---|
| numpy | < 2.0 | SD y mediapipe rompen con numpy 2.x |
| protobuf | 4.25.8 (< 5.0) | 6.x rompe serialización mediapipe |
| opencv-python | < 4.13 | 4.13+ requiere numpy 2+ |
| onnx | 1.18.0 | 1.20+ elimina float32_to_bfloat16, crash en engine builds |
| peft | 0.6.0+ | Obligatorio para StreamV2V / cached attention |
| diffusers | fork varshith15 | DEBE ser el fork, no vanilla. El installer lo maneja |

Fix universal para dependencias: python -m sd_installer repair

---

## RTX 50-Series

- CUDA 12.8 es OBLIGATORIO
- Puede necesitar múltiples intentos de instalación
- TRT engine builds pueden tardar más
- Si nada funciona: probar v0.2.99 (algunos reportan mejor soporte)
- 5070/5070 Ti: resultados mixtos
- 5090: generalmente funciona con v0.3.1 + CUDA 12.8

---

## Daydream Cloud

- Pinned a Daydream v0.2.2 (v0.2.3 tenía issue de estabilidad)
- V2V en cloud diferido a Daydream v0.2.4
- FX Processors NO disponibles en cloud
- StreamV2V NO disponibles en cloud
- Custom processors NO disponibles en cloud
