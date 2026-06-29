# POPX — Workflows y patrones

Patrones aprendidos escaneando los 54 ejemplos del pack POPX v1.2.0.
Esto documenta lo que **no está en la referencia oficial** pero sí en las redes reales.

---

## Flujo base de cualquier red POPX

```
Generator → Falloff → Modifier → Tool (Geo/Material) → Render TOP
```

Múltiples Falloffs se combinan antes del Modifier con **Combine Falloff** (Multiply, Add...).  
Múltiples Modifiers se apilan en cadena — cada uno lee el mismo o distinto falloff attribute.

---

## P1 — POPX solvers + Particle POP nativo (no se reemplazan, se complementan)

Los POPX solvers (Particle, Flow) **no gestionan emisión**. El Particle POP nativo de TD sí.

```
PointGen POP (emisor) → Particle POP nativo (lifecycle/integración)
                      + POPX Particle (física: densidad, presión, colisión)
```
POPX Particle = fuerzas y física. Particle POP nativo = emisión, edad, muerte.

---

## P2 — Feedback POP para movimiento acumulativo

Sin Feedback POP, Advect aplica el campo solo una vez.  
Con Feedback, cada frame **acumula** el desplazamiento:

```
Instancer → Noise Falloff → Noise Modifier → Advect
                                               ↓
                                         Feedback POP ← (output vuelve al Advect)
```

---

## P3 — Double Instancer con Trail POP intermedio

```
Instancer 1 (distribución) → Transform Modifier (animado con LFO)
  → Trail POP (genera age attribute por punto)
  → Popxto
  → Instancer 2 (instancia geometría sobre cada punto del trail)
  → Attribute Falloff (age como falloff) → Color Modifier + Transform Modifier
```
Resultado: estelas volumétricas donde cada punto del trail tiene su propia geometría.

---

## P4 — Path Tracer: Unpack obligatorio para instancias

Las instancias POPX packed **no pueden trazarse directamente**:
```
Instancer → Attribute Falloff → Unpack → Material → Path Tracer
```
El falloff attribute sobrevive al Unpack y se puede usar en Material para variar propiedades.

---

## P5 — Path Tracer: Voxelize para isosurface y volumen

```
FileIn POP → Voxelize → Path Tracer (Render Mode: Isosurface, Voxel Tracing ON)
FileIn POP → Voxelize → Path Tracer input 2 (Render Mode: Volume)
```
No se necesita Material op para estos modos. Voxelize hace la conversión.

---

## P6 — Path Tracer Glass

```
Box POP (habitación) ──┐
Sphere POP (cristal)  ──┤→ Merge → Material (glass) + Material (walls) → Path Tracer
FileIn POP (mesh) ─────┘
```
Glass: IOR (índice refracción) · Transmission = 1.0 · Roughness bajo.  
Múltiples materiales se asignan a objetos diferentes **antes** del Merge.  
SVGF denoiser en post-proceso.

---

## P7 — Explode + Infection Falloff = destrucción progresiva

```
FileIn POP → Explode (clusters K-means)
  → Infection Falloff (propaga desde seeds con el tiempo)
  → Noise Modifier (curl noise — distorsión orgánica, controlada por falloff)
  → Transform Modifier (scale down — encoge las piezas, controlado por falloff)
```
Speed CHOP + Express CHOP para controlar velocidad. Null POP para reset.

---

## P8 — Sweep con imagen como deformación

```
Text TOP (o video) → referencia en Sweep como Scale TOP y Twist TOP
Line POPs apilados → Sweep (Scale Per Curve ON, Twist Per Curve ON)
```
Cada línea se escala/tuerce según el valor del píxel en la imagen.  
Post-Sweep: `Convert → Unpack → Shape Falloff → Spring Modifier`

---

## P9 — Voxelize como instancing selectivo

Voxelize produce **dos cosas**: textura 3D + Grid POP de voxels.

```
GLSL POP (custom) → Sweep → Voxelize → Delete (solo voxels que intersectan mesh)
                                      → Instancer (boxes en posiciones de voxels válidos)
```
LookupTex para colorear según rampa.

---

## P10 — Physarum 2D con constraint mask

Setup mínimo:
```
PointGen POP → Physarum (2D) + Circle TOP (constraint volume, blanco=permitido)
→ PointSprite material → Render
```
El Circle TOP define la zona de crecimiento. Negro = bloqueado.

---

## P11 — Pivot: 4 modos distintos

- **Shift Pivot** → desplaza el pivot relativo al centro de cada instancia (ej: base del objeto)
- **Set Pivot World** → todas las instancias comparten el mismo pivot en world space
- **Shift Pivot + Shape Falloff** → control graduado de cuánto se desplaza el pivot

---

## P12 — Soft Body Strings sobre FBX skeleton

```
FBX → ImportSelect (skeleton) → SkinDeform POP (deforma mesh con animación)
Line POPs → Sweep (tubos finos) → Constraints (cloth) → Soft Body (colisión contra mesh)
```
ForceRadial POP para fuerzas adicionales. KeyboardIn para reset.

---

## P13 — Colisión interactiva pintada con mouse

```
Panel CHOP → Circle TOP → Feedback TOP (acumula) → Threshold TOP → Collision TOP 2D del POPX Particle
```
El Feedback TOP es imprescindible — sin él los círculos desaparecen cada frame.

---

## P14 — Flow con line strips (curve advection)

Flow no solo advecta puntos — también advecta line strips:
```
Grid POP (plano de line strips) → Flow (Target Particle Update ON, modo Advect)
→ LineSmooth → LineResample
```
Resultado: líneas que siguen el campo de velocidad del fluido.
