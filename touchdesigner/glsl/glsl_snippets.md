# GLSL Snippets — shader_changer_01

Copy-paste directo. Cada snippet funciona tal cual dentro del container.

**Origen:** documentación del container shader_changer_01 (junio 2026)
**Última revisión:** junio 2026

---

## Setup UV con aspect ratio

**Versión con macro (shaders mixed, requiere `uniforms_and_defines`):**
```glsl
#include <utils/uniforms_and_defines>

void main() {
    U  // → expande a: vec2 uv = vUV.xy * 2.0 - 1.0; uv.x *= u_aspect;
    // uv ya tiene aspect corregido y centrado en [−asp, asp] × [−1, 1]
}
```

**Versión manual (shaders geométricos, requiere `uniforms`):**
```glsl
#include <utils/uniforms>
out vec4 fragColor;

void main() {
    vec2 uv = vUV.xy * 2.0 - 1.0;
    uv.x *= u_aspect;
}
```

---

## Feedback loop mínimo

```glsl
#include <utils/uniforms_and_defines>
#include <utils/utils>

void main() {
    U

    // --- Tu forma nueva (lo que se añade en este frame) ---
    float d = length(uv) - (0.3 + u_audio.x * 0.1);
    float shape = exp(-abs(d) * 12.0);
    vec4 color = vec4(shape * 0.9, shape * 0.6, shape * 0.2, shape);

    // --- Feedback ---
    // Distorsión del UV para que el feedback se mueva
    vec2 vel = slope_luma(FB, vUV.xy, 0) * 0.004;
    vec2 suv = (vUV.xy - 0.5) * (1.0 + u_audio.x * 0.015) + 0.5;
    suv -= vel;

    vec4 tex = textureLod(FB, suv, 0.0);
    tex *= 0.975;  // decay: ajustar entre 0.95 (trail corto) y 0.999 (trail largo)

    // Compositing: nueva forma encima del feedback
    color = over(color, tex);

    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Variantes del decay:**
- `0.95` → trail muy corto, casi sin memoria
- `0.97` → trail medio (default razonable)
- `0.995` → trail largo, el contenido persiste varios segundos
- `0.999` → trail casi permanente, acumulación visible

---

## Raymarcher mínimo

```glsl
#include <utils/uniforms_and_defines>
#include <utils/utils>
#include <utils/SDF>
#include <utils/colors>

#define STEPS 32.

float map(vec3 p) {
    return sdGyroid(p * 1.5);  // escalar p cambia el tamaño de la estructura
}

void main() {
    U

    float z = 1.8;
    float result = 0.0;
    vec3 last_p = vec3(0.0);

    vec3 ro = vec3(0.0, 0.0, u_time * 0.4);
    vec3 rd = ray_dir(uv);

    for (int i = 0; i < int(STEPS); i++) {
        vec3 p = z * rd - ro;
        float d = map(p);
        result += exp(-d * 8.0);
        z += d * 0.7;
        last_p = p;
    }

    vec4 color = vec4(result / STEPS);
    color.w *= 2.0;
    color.rgb *= get_color(last_p) * 1.5 / max(dot(last_p.xy, last_p.xy), 0.1);
    color *= 1.0 + get_stripe(last_p) * 6.0;

    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Para cambiar la geometría, sustituir `map()`:**
```glsl
// Toro
float map(vec3 p) { return sdTorus(p, vec2(0.5, 0.15)); }

// Caja fractal (Menger)
float map(vec3 p) { return sdSponge(p); }

// Fusión suave de dos formas
float map(vec3 p) {
    float a = sdSphere(p - vec3(0.3, 0.0, 0.0), 0.3);
    float b = sdBox(p + vec3(0.3, 0.0, 0.0), vec3(0.2));
    return smin(a, b, 0.3);
}
```

---

## Audioreactividad — cómo conectar uniforms de audio

**Los uniforms disponibles (de `utils/uniforms` o `utils/uniforms_and_defines`):**
```glsl
uniform vec4 u_audio;       // .x=bass  .y=mid  .z=hi  .w=total (valores 0–1 aprox)
uniform vec4 u_audio_speed; // velocidad acumulada (integral del audio)
```

**Patrones más usados:**

```glsl
// Modular el tamaño de una forma con bass
float r = 0.3 + u_audio.x * 0.15;

// Modular velocidad del tiempo con total
float t = u_time + u_audio_speed.w * 0.3;

// Modular densidad visual con mid
float density = 6.0 + u_audio.y * 4.0;

// Zoom del feedback con bass
vec2 suv = (vUV.xy - 0.5) * (1.0 + u_audio.x * 0.03) + 0.5;

// Franja de brillo que late con el audio (requiere utils/colors y last_p del raymarcher)
color *= 1.0 + get_stripe(last_p) * (4.0 + u_audio.z * 6.0);
```

**`get_stripe(p)`** — función de `utils/colors` que devuelve una franja brillante que late con `u_audio_speed.w` (energía acumulada) y `u_audio.z` (hi). Especialmente efectiva en raymarchers donde `p` es la posición 3D del último punto alcanzado.

---

## Tiling — ejemplos mínimos

**tileBrick (grid de ladrillos):**
```glsl
#include <utils/uniforms>
#include <utils/tiling>
out vec4 fragColor;

void main() {
    vec2 uv = vUV.xy * 2.0 - 1.0;
    uv.x *= u_aspect;

    vec4 tile = tileBrick(uv, 4.0);  // scale=4 → 4 tiles en altura
    // tile.xy = posición local dentro del tile (−0.5 a 0.5)
    // tile.zw = ID del tile (entero como float)

    float id = getID(tile.zw);  // hash único por tile
    float pattern = step(0.4, abs(tile.x)) * step(0.4, abs(tile.y));

    vec4 color = vec4(id, id * 0.7, id * 0.4, pattern);
    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**tileHex (grid hexagonal):**
```glsl
vec4 tile = tileHex(uv, 3.0);  // scale=3

float d = length(tile.xy);  // distancia al centro del hex
float hex_shape = step(d, 0.45);

float id = getID(tile.zw);
vec4 color = vec4(hex_shape * id, hex_shape * id * 0.5, hex_shape, hex_shape);
```

**tileTruchet (Truchet con noise animado):**
```glsl
vec4 tile = tileTruchet(uv, 3.0, u_time, 8.0, 0.05);
// tile.xy = local, tile.z = ángulo de arco (0 o PI/2), tile.w = variante

// Dibujar el arco
float arc_r = 0.5;
float arc = abs(length(tile.xy - vec2(0.5 * sign(tile.z), -0.5 * sign(tile.z))) - arc_r);
float line = exp(-arc * 30.0);

vec4 color = vec4(line, line * 0.8, line * 0.5, line);
```

---

## Output siempre con dither + swizzle

Todo shader debe terminar con estas dos líneas (en ese orden):
```glsl
color = TDDither(color);            // elimina banding en gradientes
fragColor = TDOutputSwizzle(color); // corrección de canales para TD
```

Si el shader no tiene un `vec4 color` acumulado, construirlo antes:
```glsl
fragColor = TDOutputSwizzle(TDDither(vec4(result, result, result, 1.0)));
```
