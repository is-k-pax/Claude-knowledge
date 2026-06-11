# TouchDesigner LOPs — STT / TTS: patrones y pitfalls

> Conocimiento reutilizable del stack de voz en proyectos LOPs (SideCar + voice_activity + stt_transcription + tts).
> Destilado de experiencia en producción real (junio 2026).

---

## Puerta half-duplex por señal RMS (patrón producción)

**Problema:** en una sala con altavoces y micrófono abierto, el STT transcribe el TTS del propio agente → el agente se responde a sí mismo → bucle.

**Por qué la AEC nativa no siempre es suficiente:** requiere `livekit` instalado en el venv del SideCar. Si no está, `voice_activity1` falla en silencio y trabaja sin AEC. Incluso con AEC, una puerta half-duplex es más robusta y predecible.

**Solución — gate por señal digital del TTS:**

```
null_tts_out   = null CHOP       recoge out0 del operador TTS (señal digital, no acústica)
tts_rms        = analyze CHOP    function=rmspower  sobre null_tts_out
tts_hold       = lag CHOP        lag1=0.02s (ataque) lag2=0.7s (release)
mic_gate       = math CHOP       gain expr: 0 if op('tts_hold')[0] > 0.005 else 1
```

**Cableado:** `mic_in → mic_gate → {voice_activity1 in0, stt_transcription in0}`

**Por qué funciona:**
- Mide la señal digital de salida del TTS (no el rebote acústico del micrófono).
- El ataque rápido (0.02s) cierra el gate **antes** de que el sonido llegue físicamente al micrófono.
- El release lento (0.7s) evita que el micro abra durante silencios breves entre frases del TTS.
- Threshold 0.005 es robusto frente al ruido ambiente (silencio ≈ 0.00006, habla normal 0.011–0.13).

**Trade-off:** half-duplex. Si el usuario habla mientras suena el TTS, no se le escucha. Para instalaciones de sala guiada esto es preferible a un duplex caótico.

---

## `tts1.Playbackactive=False` — el default silencioso

**Síntoma:** el TTS no suena en modo `chop`, sin ningún error visible en ningún sitio.

**Causa:** el parámetro `Playbackactive` tiene default `False`. En modo `chop` el TTS no reproduce si no está activado explícitamente.

**Fix:** establecer `Playbackactive=True` en el operador TTS y persistirlo en el DAT de inicialización del pipeline (`onStart` o `_activate_engines`):
```python
op('tts1').par.Playbackmode = 'chop'
op('tts1').par.Playbackactive = True
op('tts1').par.Volume = 1.0
```

---

## AEC de `voice_activity1` requiere `livekit` en el venv

**Síntoma:** log al cargar el proyecto: `AEC dependency missing: No module named 'livekit'. Install livekit...`. La AEC no funciona aunque `Enableaec=True`.

**Causa:** `voice_activity1` incluye AEC opcional de LiveKit, pero el paquete debe estar en el **venv del SideCar** (el que apunta `ChatTD.par.Python Venv`), no en el Python del sistema.

**Fix:**
```
Python Manager → Open Console
(venv) > pip install livekit livekit-agents
```
Verificar después: `voice_chops.aec_active = 1` cuando el TTS está sonando.

---

## `ChainedCallbacksExt.callbackDat` queda vacío tras reload

**Síntoma:** callbacks del operador STT o TTS no disparan en silencio tras recargar el proyecto o hacer `reinitextensions`.

**Causa:** el campo `callbackDat` de `ChainedCallbacksExt` queda vacío en ciertas operaciones de recarga.

**Fix:** reasignarlo explícitamente en el DAT de inicialización del pipeline:
```python
op('stt_transcription').ChainedCallbacksExt.callbackDat = op('emptyCallbacks_interno')
```
Donde `emptyCallbacks_interno` es el DAT de callbacks vacío propio del operador `stt_transcription` (no uno externo).

---

## faster-whisper cae a CPU silenciosamente si CUDA no está disponible

**Síntoma:** `stt_transcription` configurado con `Device=cuda` pero la latencia es de 10-20s por frase. No hay error visible. `large-v3` en CPU es extremadamente lento.

**Causa:** si `ctranslate2` no puede acceder a CUDA (libs no instaladas en el venv, GPU saturada, CUDA no disponible en ese entorno), faster-whisper cae silenciosamente a CPU. `large-v3` en CPU puede tardar 15-30s por frase corta.

**Cómo verificar:**
```python
# En Python Manager → Open Console:
import torch
print(torch.cuda.is_available())    # False si hay problema
import ctranslate2
print(ctranslate2.get_cuda_device_count())
```

**Opciones de fix:**
1. **Modelo más pequeño** (más rápido): `stt_transcription.par.Model = 'base'` o `'small'`. Latencia ~1-2s en CPU. Precisión inferior pero suficiente para muchos casos de uso.
2. **Parakeet** (recomendado para CPU): `stt_transcription.par.Provider = 'parakeet'`. Optimizado para CPU, soporta multilingüe (~600M parámetros). Latencia ~1-2s.
3. **GPU real**: instalar `ctranslate2` con CUDA en el venv LOPs; cerrar procesos que saturen VRAM (Ollama, etc.).

---

## Filtro de alucinaciones STT en español — stopwords

**Síntoma:** frases largas y legítimas del usuario aparecen filtradas como alucinación. El log muestra `BLOQUEADO (loop)`.

**Causa:** faster-whisper (y otros modelos STT) generan alucinaciones de texto que se detectan por patrones de repetición. Un umbral de "3+ repeticiones de cualquier palabra" funciona en inglés, pero en español las palabras funcionales (artículos, preposiciones, conjunciones) se repiten naturalmente en frases normales. "la", "que", "de", "una", "en", "y" aparecen 3+ veces en cualquier frase de 10+ palabras.

**Fix — filtro español-aware:**
```python
STOPWORDS_ES = {"la", "el", "los", "las", "un", "una", "unos", "unas",
                "de", "del", "al", "en", "con", "por", "para", "que",
                "y", "o", "a", "se", "le", "lo", "me", "te", "nos",
                "es", "son", "está", "están", "hay", "su", "sus"}

def _has_pathological_loop(text, threshold=5):
    words = text.lower().split()
    content_words = [w for w in words if w not in STOPWORDS_ES and len(w) > 2]
    counts = Counter(content_words)
    return any(v >= threshold for v in counts.values())
```
- Excluir stopwords del conteo de repeticiones.
- Subir el umbral de repetición a 5+ (no 3) para palabras de contenido.
- Añadir un segundo filtro por ratio: si ≥80% de las palabras son de una lista de "hallucination words" conocidas Y el transcript tiene ≥4 palabras → bloquear.

---

## Instalación de dependencias en el venv del SideCar LOPs

El SideCar de LOPs corre en el venv apuntado por `ChatTD.par.Python Venv`. Instalar en el Python del sistema o en otro venv no tiene ningún efecto.

**Procedimiento correcto:**
```
Python Manager LOP → botón "Open Console"
# Verás el venv activado:
(venv) C:\...\LOPS_install>
pip install <paquete>
```

**Si hay WinError 5 (acceso denegado sobre un .pyd):**
1. Cerrar TouchDesigner completamente.
2. Matar workers zombies: `taskkill /F /IM python.exe`
3. Reinstalar.
4. Si persiste: reiniciar el PC (garantiza que ningún proceso tiene el `.pyd` bloqueado).

**Causa del WinError 5:** TD y sus subprocesos SideCar tienen numpy/torch importados en memoria. Windows bloquea el `.pyd` mientras está en uso. Cerrar solo la ventana de TD no siempre mata los workers.

**Nota numpy/torch:** actualizar numpy puede romper ABI con Resemblyzer, Silero VAD, EfficientWord-Net u otras libs ML del venv. Si algo falla tras una actualización de numpy, actualizar también torch/torchaudio desde la misma consola.

---

## Debounce en turn_send: cuándo es necesario y cuándo no

El VAD moderno (`voice_activity1`) gestiona la espera de silencio internamente via `Minsilenceduration`. Un debounce timer externo adicional es redundante y añade latencia.

**Patrón actual (correcto):** `turn_send_exec` escucha directamente el canal `on_speech_end` de `voice_chops`. Sin debounce timer intermedio.

**Cuándo SÍ puede necesitarse un debounce:** si el STT tiene latencia muy alta y el VAD dispara antes de que llegue la transcripción. En ese caso, mejor arreglar la latencia del STT (modelo más pequeño, GPU) que añadir debounce como parche.
