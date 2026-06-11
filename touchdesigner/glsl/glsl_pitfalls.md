# GLSL Pitfalls — shader_changer_01

Errores y trampas concretas al escribir shaders para el container. Antes de asumir que tu lógica está mal, revisa esta lista.

**Origen:** documentación del container shader_changer_01 (junio 2026)
**Última revisión:** junio 2026

---

## `#version` — NO incluir

**Síntoma:** error de compilación críptico en la primera línea.
**Causa:** TouchDesigner inyecta la directiva `#version` automáticamente. Si la añades tú, TD la duplica y GLSL falla.
**Fix:** eliminar cualquier `#version` del shader.

---

## `out vec4 fragColor` — declaración duplicada

**Síntoma:** error de compilación: `'fragColor' already declared`.
**Causa:** `#include <utils/uniforms_and_defines>` ya declara `out vec4 fragColor`. Si el shader también la declara manualmente, hay duplicado.
**Fix:**
- Si incluyes `uniforms_and_defines` → NO declares `fragColor` en el shader.
- Si solo incluyes `uniforms` (sin defines) → SÍ declarar `fragColor` manualmente.

---

## `TDOutputSwizzle` — olvidarlo silencia el output

**Síntoma:** el shader compila pero el output tiene canales de color mezclados o el alpha incorrecto.
**Causa:** TD necesita el swizzle de canales en el output final.
**Fix:** siempre cerrar con `fragColor = TDOutputSwizzle(color);`, no con `fragColor = color;`.

---

## `TDDither` — no ponerlo antes del output

**Síntoma:** banding visible en gradientes suaves (escalones de color).
**Causa:** gradientes de 8 bits sin dithering muestran la cuantización.
**Fix:** añadir `color = TDDither(color);` justo antes de `TDOutputSwizzle`. Si el shader lo omite, los gradientes se ven escalonados.

---

## `PI` incorrecto en `uniforms_and_defines`

**Síntoma:** cálculos con PI dan resultados ligeramente incorrectos en ángulos.
**Causa:** el valor definido en el utils es `3.14151` en lugar de `3.14159265358979`.
**Fix:** si necesitas PI preciso, declarar localmente en el shader:
```glsl
#define PI_REAL 3.14159265358979
```
Para la mayoría de efectos visuales, la diferencia no es perceptible.

---

## `ray_dir` — perspectiva ortogonal, no perspectiva real

**Síntoma:** el raymarcher no produce la perspectiva convergente que esperabas.
**Causa:** `ray_dir(uv)` en `SDF.glsl` simplemente devuelve `normalize(vec3(uv, 1.0))`. Es una proyección ortogonal, no una cámara con FOV real.
**Fix esperado:** esto es por diseño en el container. Si necesitas perspectiva real, calcular `rd` manualmente:
```glsl
float fov = 1.5;  // menor = más campo de visión
vec3 rd = normalize(vec3(uv / fov, 1.0));
```

---

## Macro `U` — no usar en A.glsl / B.glsl

**Síntoma:** compilación correcta pero UV incorrecto en los shaders de máscara de transición.
**Causa:** A.glsl y B.glsl no incluyen `uniforms_and_defines` y calculan UV como `vUV.xy - 0.5` (sin el factor 2 ni el aspect).
**Fix:** esta diferencia es intencional — los presets de usuario sí usan la macro `U`. Solo A.glsl y B.glsl usan el UV manual.

---

## `#include <utils/X>` — resolución relativa al DAT, no al GLSL TOP

**Síntoma:** el shader en un subcontainer (`mixed_shaders_1/`, `geometric_shaders_1/`) no puede resolver `utils/X`.
**Causa:** `#include` resuelve relativo a la ubicación del DAT fuente, no del GLSL TOP que lo carga. Un shader en `mixed_shaders_1/mi_shader` busca `mixed_shaders_1/utils/X`, que no existe.
**Fix:** los shaders se cargan vía el selectDAT `A` que actúa de intermediario en el nivel del container donde sí existe `utils/`. Los shaders creados directamente dentro de subcontainers sin pasar por ese intermediario no pueden resolver los includes.

---

## `u_time` — no existe builtin, es un uniform

**Síntoma:** error `'u_time' undefined` o shader sin animación.
**Causa:** a diferencia de Shadertoy (`iTime`), TD GLSL no tiene un builtin de tiempo. El tiempo se pasa como `uniform float u_time` desde el container.
**Fix:** incluir `utils/uniforms` o `utils/uniforms_and_defines`. Si estás fuera del container y necesitas tiempo, crear el uniform manualmente en el GLSL TOP.

---

## `uTDOutputInfo.res.zw` — resolución de output

Para leer la resolución en el shader (útil para calcular aspect ratio manualmente si no tienes el uniform):
```glsl
vec2 res = uTDOutputInfo.res.zw;  // .zw = width, height
float aspect = res.x / res.y;
```
No usar `res.xy` — esos son otros campos.

---

## `dFdx` / `dFdy` — solo disponibles en fragment shaders

Las derivadas de pantalla `dFdx()` y `dFdy()` están disponibles en GLSL TOP (fragment) y se usan en los shaders `fb_*` para calcular la velocidad del gradiente. Son estándar GLSL, no hay trampa — recordar que en GLSL ES 2.0 necesitan la extensión, pero TD la incluye automáticamente.

---

## `textureLod` con lod > 0 — blur intencional del feedback

```glsl
vec4 tex = textureLod(FB, suv, 2.0);  // lod 2 = blurreado
```
Esto no es un error — es una técnica deliberada. El lod alto hace blur del feedback, creando el efecto de trail suavizado que se ve en los shaders `fb_*`. Si el trail se ve borroso inesperadamente, verificar el valor de lod.

---

## `TDSimplexNoise` — no es `texture()`, es una función builtin TD

`TDSimplexNoise(vec3 p)` devuelve un float en [-1, 1] aproximadamente. Es un builtin de TD, no necesita include ni textura. Los macros `NOISE1/2/3` en `uniforms_and_defines` son wrappers de esta función.
