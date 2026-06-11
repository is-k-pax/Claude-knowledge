# GLSL Writing Patterns — shader_changer_01

Recetas para crear presets compatibles con el container. Cada patrón describe qué tipo de visual produce, qué utils necesita, un esqueleto mínimo funcional y cómo añadir audioreactividad.

**Origen:** documentación del container shader_changer_01 (junio 2026)
**Última revisión:** junio 2026

---

## Cómo crear un preset nuevo compatible con el container

1. Crear un Text DAT en `geometric_shaders_1/` o `mixed_shaders_1/` (el nombre = nombre del preset)
2. El sistema lo detecta automáticamente vía `op('names')`
3. Reglas de output obligatorias:
   - Siempre terminar con `color = TDDither(color);` antes de la línea final
   - Siempre cerrar con `fragColor = TDOutputSwizzle(color);`
4. `out vec4 fragColor` ya está declarada en `uniforms_and_defines`. Si incluyes ese DAT, NO redeclararla. Si usas solo `uniforms`, declararla manualmente.
5. Nunca añadir `#version` — TD lo inyecta solo.

---

## Patrón 1: Geométrico simple (sin feedback)

**Produce:** formas geométricas nítidas, fractales acumulativos, bandas de color por sin(). Visual duro y limpio.

**Cuándo usarlo:** shaders sin estado, que se calculan fresh cada frame. Sin persistencia ni trails.

**Utils a incluir:**
```glsl
#include <utils/uniforms>       // obligatorio
#include <utils/easing>         // si usas accumulateGain
#include <utils/IQ_SDF>         // formas 2D precisas
// o <utils/SDF> para SDFs 3D y smin
out vec4 fragColor;              // declarar manualmente (uniforms no la incluye)
```

**Esqueleto:**
```glsl
#include <utils/uniforms>
#include <utils/easing>
#include <utils/IQ_SDF>
out vec4 fragColor;

void main() {
    vec2 uv = vUV.xy * 2.0 - 1.0;
    uv.x *= u_aspect;

    float t = u_time;
    float result = 0.0;

    // Patrón band_look: loop fractal acumulativo
    vec2 c = uv;
    for (int i = 0; i < 6; i++) {
        c = abs(c) / dot(c, c) - 0.9;
        result += exp(-abs(c.x) * 5.0) * 0.3;
    }

    vec3 col = vec3(
        sin(result * 3.0 + t),
        sin(result * 2.0 + t + 2.0),
        sin(result * 4.0 + t + 4.0)
    ) * 0.5 + 0.5;

    vec4 color = vec4(col * result, result);
    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Variables clave para variar:**
- Número de iteraciones del loop → más = más detalle fractal
- El divisor en `dot(c,c) - X` → cambia la forma del atractor
- Los multiplicadores del sin() del color → cambia las armónicas de color
- `u_time * speed` → velocidad de animación

**Audioreactividad:**
```glsl
// Modular la densidad del fractal
float density = 5.0 + u_audio.x * 3.0;   // bass expande las bandas
result += exp(-abs(c.x) * density) * 0.3;

// Modular la velocidad
float t = u_time + u_audio_speed.w * 0.5;
```

---

## Patrón 2: Mixed con feedback

**Produce:** trails persistentes, smearing, partículas que se acumulan, warp orgánico. Visual fluido con memoria temporal.

**Cuándo usarlo:** efectos que necesitan que el frame anterior se mezcle con el nuevo (feedback loop).

**Utils a incluir:**
```glsl
#include <utils/uniforms_and_defines>  // incluye FB, RAND, macro U, y declara fragColor
#include <utils/utils>                 // over(), slope_luma(), luma_tex()
#include <utils/SDF>                   // si usas SDFs en la lógica
#include <utils/colors>                // si usas get_stripe() o get_color()
```

**Esqueleto:**
```glsl
#include <utils/uniforms_and_defines>
#include <utils/utils>

void main() {
    U   // inicializa: vec2 uv con aspect corregido

    // Generar la forma nueva del frame actual
    float d = length(uv) - 0.3;
    float shape = exp(-abs(d) * 10.0);
    vec4 color = vec4(shape * 0.8, shape * 0.5, shape * 0.2, shape);

    // Calcular UV distorsionado para samplear el feedback
    float asp = u_aspect;
    vec2 vel = slope_luma(FB, vUV.xy, 0) * 0.005;
    vec2 suv = (vUV.xy - 0.5) * (1.0 + u_audio.x * 0.02) + 0.5;
    suv -= vel;

    // Samplear feedback y mezclar
    vec4 tex = textureLod(FB, suv, 0.0);
    tex *= 0.97;  // decay: 0.95 = trail corto, 0.999 = trail muy largo
    color = over(color, tex);  // nuevo frame encima del feedback

    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Variables clave para variar:**
- `decay` (0.95 – 0.999) → longitud del trail
- `vel` y su escala → velocidad del warp del feedback
- `lod` en `textureLod` → blur del trail (lod > 0 suaviza)
- El offset de suv con audio → cuánto se mueve el feedback con el bass

**Audioreactividad:**
```glsl
vec2 suv = (vUV.xy - 0.5) * (1.0 + u_audio.x * 0.05) + 0.5;  // zoom con bass
suv -= slope_luma(FB, vUV.xy, 0) * u_audio.w * 0.003;          // warp con total
```

---

## Patrón 3: Raymarcher

**Produce:** geometría 3D volumétrica, nube de densidad, estructuras infinitas. Visual con profundidad.

**Cuándo usarlo:** cualquier cosa que necesite recorrer un campo 3D (gyroids, tomos, cajas, fractales 3D).

**Utils a incluir:**
```glsl
#include <utils/uniforms_and_defines>  // FB, RAND, U, fragColor
#include <utils/utils>
#include <utils/SDF>                   // sdGyroid, sdBox, sdSponge, ray_dir, smin
#include <utils/colors>                // get_color(), get_stripe()
```

**Esqueleto:**
```glsl
#include <utils/uniforms_and_defines>
#include <utils/utils>
#include <utils/SDF>
#include <utils/colors>

#define STEPS 32.

float map(vec3 p) {
    return sdGyroid(p);   // sustituir por la SDF que quieras
}

void main() {
    U

    float z = 1.8;
    float result = 0.0;
    vec3 last_p = vec3(0.0);

    vec3 ro = vec3(0.0, 0.0, u_time * 0.5);  // origen del rayo avanza en z
    vec3 rd = ray_dir(uv);                    // dirección desde UV (ortogonal)

    for (int i = 0; i < int(STEPS); i++) {
        vec3 p = z * rd - ro;
        float d = map(p);
        result += exp(-d * 8.0);
        z += d * 0.8;
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

**Variables clave para variar:**
- La SDF en `map()` → `sdGyroid`, `sdTorus`, `sdBox`, `sdSponge`, combinaciones con `smin`
- Transformaciones a `p` dentro del loop: `fract()`, `rot()`, `abs()` → infinito tileado, simetría, fractales
- `density` en `exp(-d * density)` → qué tan denso/opaco aparece el volumen
- `step_scale` en `z += d * step_scale` → calidad del raymarching

**Audioreactividad:**
```glsl
// Modular el parámetro de la SDF con audio
float power = 2.0 + u_audio.x * 2.0;      // bass cambia la forma
float d = sdBox(p, vec3(0.3 + u_audio.y * 0.2, 0.3, 0.3));

// Velocidad de avance reactiva al total
vec3 ro = vec3(0.0, 0.0, u_time * 0.3 + u_audio_speed.w * 0.1);
```

---

## Patrón 4: Rectangles / lines con u_noise

**Produce:** líneas y rectángulos generativos, divisiones del espacio que cambian suavemente. Visual minimal, geométrico, animado por noise lento.

**Cuándo usarlo:** cuando quieres cortes de espacio orgánicos pero geométricos, que mutan sin ser bruscos.

**Utils a incluir:**
```glsl
#include <utils/uniforms>    // u_noise vive aquí
#include <utils/easing>      // zigzag para variaciones
out vec4 fragColor;
```

**Esqueleto:**
```glsl
#include <utils/uniforms>
out vec4 fragColor;

void main() {
    vec2 uv = vUV.xy * 2.0 - 1.0;
    uv.x *= u_aspect;

    // u_noise.xy y u_noise.zw son dos puntos de corte animados
    vec2 p1 = uv - u_noise.xy;
    vec2 p2 = uv - u_noise.zw;

    float h1 = smoothstep(-0.01, 0.01, p1.x) * 2.0 - 1.0;
    float v1 = smoothstep(-0.01, 0.01, p1.y) * 2.0 - 1.0;
    float h2 = smoothstep(-0.01, 0.01, p2.x) * 2.0 - 1.0;
    float v2 = smoothstep(-0.01, 0.01, p2.y) * 2.0 - 1.0;

    // Combinaciones: min = intersección, max = unión, * = rectángulo
    float r1 = min(h1, v1);         // esquina positiva
    float r2 = h1 * v2;             // rectángulo diagonal
    float result = max(r1, -r2);    // componer

    vec4 color = vec4(result * 0.5 + 0.5, result * 0.5 + 0.5, result * 0.5 + 0.5, 1.0);
    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Variables clave para variar:**
- Las operaciones entre `h1`, `v1`, `h2`, `v2`: `min`, `max`, `*`, `abs(h-v)` → distintas formas
- El ancho del smoothstep (`-0.01, 0.01`) → grosor de la línea

**Audioreactividad:**
```glsl
float thickness = 0.005 + u_audio.z * 0.02;  // hi expande las líneas
float h1 = smoothstep(-thickness, thickness, p1.x) * 2.0 - 1.0;
```

---

## Patrón 5: Domain Warp FBM

**Produce:** texturas orgánicas fluidas, nubes, lava, formas que se derriten. El domain warping hace que el noise se pliegue sobre sí mismo creando estructuras complejas.

**Cuándo usarlo:** fondos orgánicos, flujos, cualquier cosa que necesite movimiento fluido sin SDFs.

**Utils a incluir:**
```glsl
#include <utils/uniforms_and_defines>  // GET_COL para colorear, fragColor
#include <utils/utils>
```

**Esqueleto:**
```glsl
#include <utils/uniforms_and_defines>
#include <utils/utils>

float fbm(vec3 p) {
    float w = 1.0, f = 1.0, n = 0.0;
    for (int i = 0; i < 6; i++) {
        n += TDSimplexNoise(p * f + float(i)) * w;
        w *= 0.7;
        f *= 1.9;
        p.z += n * 0.6;  // warp en z → la clave del domain warp
    }
    return n * n * 2.0;
}

void main() {
    U

    vec3 p = vec3(uv * 0.5, u_time * 0.1);
    float d = fbm(p);

    vec3 col = GET_COL(p.zxy * 0.5, d);
    float alpha = smoothstep(0.0, 0.3, d);

    vec4 color = vec4(col * d, alpha);
    color = TDDither(color);
    fragColor = TDOutputSwizzle(color);
}
```

**Variables clave para variar:**
- Número de octavas del loop → más = más detalle
- `w *= X` (0.6–0.92) → balance entre octavas (lacunarity weight)
- `f *= X` (1.7–2.0) → frecuencia de cada octava
- `p.z += n * X` (0.5–0.75) → intensidad del domain warp
- `n * n * factor` → exponente y escala del resultado final

**Audioreactividad:**
```glsl
float speed = 0.1 + u_audio_speed.w * 0.05;
vec3 p = vec3(uv * 0.5, u_time * speed);

// Modular el warp con el bass
p.z += n * (0.6 + u_audio.x * 0.4);
```
