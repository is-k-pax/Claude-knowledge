# SD Diagnóstico Rápido
Léeme PRIMERO cuando el usuario dice que algo falla. Coste: ~400 tokens.

## Árbol de decisión

### "No genera nada / frames negros"
1. ¿Prompt weights suman 0? → Al menos un prompt con weight > 0
2. ¿IP Adapter ON + sd-turbo? → INCOMPATIBLE. sd-turbo es SD 2.1, IP Adapter necesita SD 1.5 o SDXL
3. ¿Error de sesión anterior? → Restart stream

### "Acceleration has failed"
1. Borrar carpeta engines/td/ y rebuild
2. ¿IP Adapter ON con sd-turbo? → Desactivar IP Adapter
3. ¿Cambió modelo/CN/IPA desde último build? → Rebuild obligatorio

### "ControlNet no hace efecto"
1. ¿CN activado ANTES de start stream? → Obligatorio
2. ¿CN weight > 0? → Verificar
3. ¿Modelo CN coincide con base? → SDXL base necesita CN SDXL, SD1.5 base necesita CN SD1.5
4. ¿Input conectado al input 2? (modo local) → Verificar
5. ¿Autopreprocess ON sobreescribiendo selección manual? → Desactivar si quieres manual

### "IP Adapter no funciona"
1. ¿Activado ANTES de start stream? → Obligatorio
2. ¿Modelo base es sd-turbo? → NO compatible (SD 2.1)
3. ¿IP Adapter Scale > 0? → Verificar
4. ¿Se ha pulsado IP Adapter Update? → Obligatorio tras cambiar imagen

### "StreamV2V / Cached Attention no funciona"
1. ¿Acceleration = tensorrt? → OBLIGATORIO, sin TRT no funciona
2. ¿Scheduler = tcd? → OBLIGATORIO para cached attention
3. ¿Activado ANTES de start stream? → Obligatorio
4. ¿Resolución cambió desde engine build? → V2V está LOCKED a resolución del engine
5. ¿peft instalado? → Verificar con sd_installer verify

### "FPS muy bajo"
1. ¿TensorRT activado? → Si no, activar
2. ¿Dual ControlNet? → En 24GB GPU ya va a 4-9 FPS, normal
3. ¿depth CPU en vez de depth_tensorrt? → CPU usa ~5GB extra y 60% más lento
4. ¿Resolución > 512? → Bajar
5. ¿SDXL vs sd-turbo? → sd-turbo más ligero

### "CUDA out of memory"
1. Consultar sd_hardware_configs.md para VRAM budget de tu GPU
2. Usar Unload Models pulse
3. Desactivar IP Adapter (+4.3GB)
4. Usar single CN en vez de dual
5. Usar depth_tensorrt en vez de depth CPU
6. Bajar resolución
7. sd-turbo en vez de SDXL

### "Engine TRT: ¿está bien o mal hecho?"
Un engine válido:
- Pesa entre 1-8 GB dependiendo del modelo y features
- Se carga sin errores en <30s tras primer build
- Primer build tarda 20-30 min (normal)
Un engine corrupto o desactualizado:
- Crash al cargar o "Acceleration has failed"
- Se creó con config diferente (modelo/CN/IPA distintos)
- FIX: borrar engines/td/ completo y rebuild

### "¿Necesito rebuild del engine TRT?"
SÍ rebuild si cambias: modelo, ControlNet on/off, IP Adapter on/off
NO rebuild si cambias: resolución (384-1024), step count (1-4)
EXCEPCIÓN: StreamV2V engines están locked a resolución del build
