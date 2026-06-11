# GLSL Container Architecture — shader_changer_01

Descripción de cómo está construido el container `shader_changer_01` para que Claude entienda el contexto antes de modificar nada.

**Origen:** documentación del container shader_changer_01 (junio 2026)
**Última revisión:** junio 2026

---

## Qué es este container

Un container de TouchDesigner que actúa como **sistema modular de shaders GLSL audioreactivos**. Permite tener múltiples "presets" en una sola red, con transiciones suaves, reactividad de audio y una arquitectura de utils compartida via `#include`.

---

## Estructura general

```
shader_changer_01/
├── utils/                        ← DATs con código GLSL compartido (#include)
├── geometric_shaders_1/          ← presets de shaders geométricos
├── mixed_shaders_1/              ← presets de shaders mixtos/orgánicos
├── transition/ (Base COMP)       ← CHOPs de audio y control de transición
├── glsl_A / glsl_B               ← Los dos GLSL TOP activos (A/B swap)
├── switch3                       ← Elige geometric vs mixed
├── null2                         ← Pasa el output del switch
├── glsl1                         ← Post-process: edge + brightness + invert + mono
├── glsl2                         ← Composite: mezcla shader con input externo
└── glsl3                         ← Genera textura de ruido/hash para RAND
```

---

## Sistema de presets — cómo funciona el swap A/B

El mecanismo central está en `parexec1` (Python):

```python
def onValueChange(par, prev):
    if par.name == 'Index':
        toggle = parent.simples.storage['AB']      # alterna entre A y B
        op('constant1').par.const0value = not(toggle)
        shader_comp = parent().par.Shaderscomp.eval()
        shader_name = op('names')[index, 0]
        if toggle:
            op('A').par.dat = f"{shader_comp}/{shader_name}"  # actualiza A
        else:
            op('B').par.dat = f"{shader_comp}/{shader_name}"  # actualiza B
        parent.simples.storage['AB'] = not(toggle)
```

**El truco del cross-fade sin glitch:** en lugar de recompilar el mismo GLSL TOP, se actualiza el GLSL que **no está siendo mostrado actualmente**, y luego se hace el cross-fade. Así la transición es suave y sin artefacto de compilación.

El parámetro `premade_shaders` (0=mixed, 1=geometric) controla qué carpeta está activa via `parexec2`:
```python
if int(par) == 0:
    parent().par.Shaderscomp = "./mixed_shaders_1"
if int(par) == 1:
    parent().par.Shaderscomp = "./geometric_shaders_1"
```

---

## Shaders de la máscara de transición (A.glsl y B.glsl)

Son los shaders de la **máscara** para el efecto de transición, no los presets de usuario. Usan `accumulateGain` para un tiempo que hace zigzag, y `mix4()` entre 4 SDFs para animar la máscara de fade.

**Nota crítica:** A.glsl y B.glsl **no usan la macro `U`** ni incluyen `uniforms_and_defines`. Declaran `fragColor` manualmente y calculan UV como `vUV.xy - 0.5`. Los presets de usuario sí usan la macro `U`.

---

## Post-process: glsl1_pixel (edge + effects)

Shader aplicado sobre el output del preset activo:

```glsl
uniform float u_edge, u_bright, u_inv, u_mono;

// Sobel edge detection → mix(color, edge_magnitude, u_edge)
// Brillo: color *= u_bright
// Inversión: mix(inverted, color, u_inv)
// Monocromático: mix(color, luminance, u_mono)
fragColor = TDOutputSwizzle(color);
```

---

## Composite: glsl2_pixel (warp por luma)

Mezcla el shader con un input externo usando la luma como distorsión de UVs:

```glsl
uniform float u_off, u_mult;
// Lee luma del input 1, la usa como offset de UVs del input 0
// suv = (vUV.xy - 0.5) * (1 + luma * 0.5 * u_off) + 0.5
// color *= color * mix(1, luma, u_mult)
```

---

## Ruido: glsl3_pixel (textura RAND)

Genera una textura de hash de alta frecuencia (blue noise style). Es el `RAND` = `sTD2DInputs[1]` que usan los raymarchers y cualquier shader que necesite ruido de alta frecuencia.

---

## Dónde viven los presets

- `geometric_shaders_1/` — shaders geométricos: band_looks, tilings, hex, truchet, gradientes
- `mixed_shaders_1/` — shaders orgánicos/mixtos: raymarchers, domain warp, feedback, líneas

El selector `switch3` elige qué carpeta está activa. Para añadir un preset nuevo, crear un DAT en la carpeta correspondiente y el sistema lo detecta automáticamente via `op('names')`.

---

## Cadena de señal

```
geometric_shaders_1/ ──┐
                        ├── switch3 ── null2 ── glsl1 (post) ── glsl2 (composite) ──► output
mixed_shaders_1/    ──┘
                                              ▲
glsl3 (RAND) ─────────────────────────────────┘ (sTD2DInputs[1] en los presets)
```

`glsl_A` y `glsl_B` son los dos GLSL TOPs que se van alternando para el cross-fade. El preset activo en cada momento está cargado en el que tiene visibilidad; el otro se precompila con el siguiente preset mientras no es visible.
