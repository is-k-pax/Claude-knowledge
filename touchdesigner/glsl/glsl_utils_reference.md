# GLSL Utils Reference — shader_changer_01

Referencia compacta de todas las funciones disponibles via `#include <utils/X>` en el container. Consultar mientras se escribe un shader para saber qué está disponible.

**Origen:** documentación del container shader_changer_01 (junio 2026)
**Última revisión:** junio 2026

---

## `#include <utils/uniforms_and_defines>`

Incluir en shaders mixed/con feedback. Ya declara `out vec4 fragColor`, así que NO redeclararla.

**Defines y macros:**
- `FB` → `sTD2DInputs[0]` — input de feedback (textura del frame anterior)
- `RAND` → `sTD2DInputs[1]` — textura de ruido/hash generada por glsl3
- `PI` → `3.14151` ⚠️ (valor incorrecto — ver glsl_pitfalls.md si necesitas PI preciso)
- `U` → setup UV en una línea: `vec2 uv = vUV.xy * 2.0 - 1.0; uv.x *= u_aspect;`
- `NOISE1(p)` → `TDSimplexNoise(p)` — float
- `NOISE2(p)` → vec2 con dos frecuencias
- `NOISE3(p)` → vec3 con tres frecuencias
- `COL_NOISE(p)` → vec3 noise remapeado a [0,1], útil para colores
- `GET_COL(p, o)` → `normalize(COL_NOISE(p - vec3(0,0,o)))` — color normalizado desde posición 3D

---

## `#include <utils/uniforms>`

Alternativa a `uniforms_and_defines` para shaders geométricos simples (sin feedback, sin macros). No declara `fragColor`.

**Uniforms disponibles:**
- `uniform float u_aspect` — aspect ratio de la resolución de salida
- `uniform float u_time` — tiempo en segundos (no hay builtin automático en TD GLSL)
- `uniform float u_intensity` — control manual de intensidad general
- `uniform vec4 u_audio` — `.x`=bass, `.y`=mid, `.z`=hi, `.w`=total
- `uniform vec4 u_audio_speed` — velocidad acumulada del audio (integral)
- `uniform vec4 u_noise` — señal de noise, usada como puntos de corte: `.xy` y `.zw`
- `uniform vec4 u_noise_vel` — gradiente de velocidad del noise

---

## `#include <utils/utils>`

Funciones de utilidad general.

| Función | Descripción |
|---|---|
| `vec4 over(vec4 fg, vec4 bg)` | Composite alpha-over correcto (premultiplied) |
| `float zigzag(float x)` | Onda triangular [0,1] |
| `mat2 rot(float a)` | Matriz de rotación 2D, a en radianes |
| `vec2 slope_red(sampler2D, vec2 uv, int lod)` | Gradiente del canal R |
| `vec2 slope_green(sampler2D, vec2 uv, int lod)` | Gradiente del canal G |
| `vec2 slope_blue(sampler2D, vec2 uv, int lod)` | Gradiente del canal B |
| `float luma(vec3 col)` | Luminancia perceptual |
| `float luma_tex(sampler2D, vec2 uv, int lod)` | Luma directamente de textura |
| `vec2 slope_luma(sampler2D, vec2 uv, int lod)` | Gradiente de luma (útil para feedback warp) |
| `vec3 safenorm3(vec3 v)` | `normalize()` sin NaN cuando v=0 |
| `vec2 safenorm2(vec2 v)` | Ídem para vec2 |

---

## `#include <utils/SDF>`

SDFs 2D, 3D y utilidades de raymarching.

**2D:**
| Función | Descripción |
|---|---|
| `float circleSDF(vec2 p, float r)` | Círculo centrado en origen |
| `float lineSDF(vec2 p, vec2 a, vec2 b)` | Distancia a segmento |
| `float smin(float a, float b, float k)` | Smooth minimum — fusiona dos SDFs suavemente |

**3D:**
| Función | Descripción |
|---|---|
| `float sdGyroid(vec3 p)` | Superficie gyroid |
| `float sdBoxFrame(vec3 p, vec3 b, float e)` | Marco de caja 3D |
| `float sdTorus(vec3 p, vec2 t)` | Toro — `t.x`=radio mayor, `t.y`=radio menor |
| `float sdBox(vec3 p, vec3 b)` | Caja con semiejes `b` |
| `float sdSphere(vec3 p, float r)` | Esfera |
| `float sdSponge(vec3 p)` | Fractal Menger sponge |

**Raymarching:**
| Función | Descripción |
|---|---|
| `vec3 ray_dir(vec2 uv)` | Dirección de rayo — devuelve `normalize(vec3(uv, 1.0))` (perspectiva ortogonal simple) |

---

## `#include <utils/IQ_SDF>`

SDFs 2D de Inigo Quilez — para formas 2D precisas.

| Función |
|---|
| `sdCircle`, `sdRoundedBox`, `sdChamferBox`, `sdBox` (2D), `sdOrientedBox` |
| `sdSegment`, `sdRhombus`, `sdEquilateralTriangle`, `sdTriangleIsosceles`, `sdTriangle` |
| `sdUnevenCapsule`, `sdPentagon`, `sdHexagon`, `sdOctogon` |
| `sdHexagram`, `sdPentagram`, `sdTrap` |
| helpers: `float ndot(vec2,vec2)`, `float dot2(vec2)` |

---

## `#include <utils/colors>`

| Función | Descripción |
|---|---|
| `vec3 rgb2hsv(vec3 c)` | Conversión RGB → HSV |
| `vec3 hsv2rgb(vec3 c)` | Conversión HSV → RGB |
| `vec3 get_color(vec3 p)` | Paleta basada en sin() del eje z — colorea raymarchers |
| `float get_stripe(vec3 p)` | Franja de brillo audioreactiva, late con `u_audio_speed.w` y `u_audio.z` |

---

## `#include <utils/easing>`

| Función | Descripción |
|---|---|
| `float zigzag(float x)` | Onda triangular (también en utils) |
| `float gain(float x, float k)` | S-curve con sesgo — k<1 expande inicio, k>1 expande final |
| `float accumulateGain(float x, float k)` | gain acumulado en el tiempo, movimiento orgánico |
| `float linearstep(float e0, float e1, float x)` | Clamp lineal sin suavizado (más sharp que smoothstep) |
| backIn/Out/InOut, bounceIn/Out/InOut | Easing clásico — Back, Bounce |
| circularIn/Out/InOut | Easing circular |
| elasticIn/Out/InOut | Easing elástico |
| sinIn/Out/InOut | Easing sinusoidal |

**Nota de uso:** `accumulateGain(u_time * speed, k)` genera tiempo con S-curve acumulativa — mucho más orgánico que `u_time` directo.

---

## `#include <utils/tiling>`

Sistemas de tiling — devuelven `vec4(local.xy, id.xy)` donde `local` es posición dentro del tile e `id` es identificador del tile.

| Función | Descripción |
|---|---|
| `float getID(vec2 id)` | Hash cantor — ID único flotante por tile |
| `vec4 tileBrick(vec2 p, float scale)` | Grid de ladrillos offset |
| `vec4 tileHex(vec2 p, float scale)` | Grid hexagonal |
| `vec4 tileHexSides(vec2 p, float scale)` | Hex con ID de sector (0,1,2) en `.w` |
| `vec4 tilePolar(vec2 p, float seg, float rings)` | Tiling polar — segmentos y anillos |
| `vec4 tileMirror(vec2 p, float scale)` | Tiling con simetría de espejo |
| `vec4 tileSpiral(vec2 p, float turns, float rings)` | Tiling espiral |
| `vec4 tileTruchet(vec2 p, float s, float time, float period, float sm)` | Truchet con noise animado |
| `vec4 tileTruchet45(vec2 p, float s, float time, float period, float sm)` | Truchet 45°, variante rotada |

---

## `#include <utils/mixing>`

Para interpolar cíclicamente entre N SDFs o valores — el motor de las animaciones morfológicas.

| Función | Descripción |
|---|---|
| `mat2 rotCycles(float a)` | Rotación donde a en [0,1] corresponde a [0, 2π] |
| `float mix3(float[3], float pct)` | Interpola cíclicamente entre 3 valores |
| `float mix4(float[4], float pct)` | Ídem 4 valores — el más usado |
| `float mix5/6/7/8(float[], float pct)` | Ídem para N valores |

**Nota de uso:** `mix4([sdf1, sdf2, sdf3, sdf4], accumulateGain(u_time, k))` es el patrón de animación morfológica por excelencia en los shaders `floating_rects`.
