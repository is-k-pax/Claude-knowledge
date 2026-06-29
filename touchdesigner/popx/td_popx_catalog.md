# POPX — Catálogo de operadores

Doc oficial: https://popx.tools/docs — v1.4.0 — 62 operadores  
Cada op tiene toggle **Help** en su página About → abre doc directamente.

**POPX Geometry:** cada punto lleva P + Rotación + Escala + Pivot. GPU-packed.  
La mayoría de ops acepta tanto POPX Geometry como POP estándar.

**Página Common** (en casi todos): Bypass · Free Extra GPU Memory · Render Primitives · SRT/RST

---

## GENERATORS (6) — crean POPX Geometry

| Op | In | Para qué |
|---|---|---|
| **Convert** | 1 | POP regular → POPX Geometry. Particiona por conectividad o piece attribute. **No calcula orientación → usar Reorient después** |
| **Explode** | 2 | Cada cara de un mesh → instancia packed orientada. K-means clustering disponible |
| **Instancer** | 1+ | Distribuye copias sobre Point Clouds, Meshes o Curves. Dos modos: **Copy to Points** (realiza geo, modificable) o **GPU Instancing** (rápido, no deformable) |
| **Planar Patch** | 1 | Genera patches planos sobre superficie |
| **Subdivider** | 1 | Subdivide geometría añadiendo resolución |
| **Sweep** | 1-2 | Barre un perfil a lo largo de una curva → geometría tubular. Scale/Twist Per Curve desde imagen TOP |

---

## FALLOFFS (13) — generan atributo de influencia (0-1 por punto)

Los Falloffs **no mueven geometría**. Generan un `falloff` attribute que los Modifiers leen.  
Cadena: `Generator → Falloff → Modifier`  
Página Falloff común: Combine Operation · Combine Strength · Output Falloff Attribute · Preview Falloff  
Página Remap común: Clamp · Fit · Invert · Ramp · Custom Ramp TOP

| Op | Para qué |
|---|---|
| **Attribute Falloff** | Usa atributo existente como falloff |
| **Channel Falloff** | Mapea CHOP channel a puntos |
| **Combine Falloff** | Combina varios falloffs (Add/Multiply/Min/Max) |
| **Curve Falloff** | Distancia a una curva |
| **Infection Falloff** ⭐ | Propagación tipo infección desde seeds. Tiene Play/Step/Initialize propio |
| **Noise Falloff** ⭐ | Ruido procedural 2D/3D/4D Perlin o Simplex. Transform stack completo |
| **Object Falloff** | Distancia a objeto 3D de TD |
| **Paint Falloff** | Pintar manualmente en viewport |
| **Preview Falloff** | Debug: visualiza falloff como color sin modificar datos |
| **Remap Falloff** | Remapea falloff existente con curvas |
| **Shape Falloff** ⭐ | SDF de esfera/box/cilindro/plano. Múltiples shapes via Specification POP |
| **Spread Falloff** | Propaga de punto a punto (N saltos, sin tiempo) |
| **Texture Falloff** | Mapea una textura TOP como falloff |

---

## MODIFIERS (13) — transforman POPX Geometry

Todos aceptan `Do Falloff` + `Falloff Attribute` para control per-instancia.

| Op | Para qué |
|---|---|
| **Advect** | Mueve puntos siguiendo un campo vectorial |
| **Aim** | Orienta instancias hacia un target |
| **Color Modifier** | Modifica atributo Cd. Set/Add/Multiply |
| **Filter** | Suaviza atributos aplicando blur sobre vecinos |
| **Magnetize** | Atrae/repele instancias hacia un punto |
| **Move Along Curve** | Mueve instancias a lo largo de una curva |
| **Move Along Mesh** | Proyecta/mueve instancias sobre superficie de mesh |
| **Noise Modifier** | Ruido procedural a posición/rotación/escala |
| **Pivot** ⭐ | Mueve el pivot. Shift Pivot (relativo) vs Set Pivot World (todos al mismo punto) |
| **Randomize** | Variación aleatoria a T/R/S. Seed-controlado |
| **Relax** | Distribuye instancias uniformemente (Lloyd relaxation) |
| **Spring Modifier** ⭐ | Física muelle. Compatible con POP estándar. stiffness/damping/rest length |
| **Transform Modifier** ⭐ | T/R/S con falloff. **Local Space ON** = ejes locales de cada instancia |

---

## TOOLS (21) — utilidades de pipeline

| Op | Para qué |
|---|---|
| **Apply Attributes** | Transfiere atributos entre POPs |
| **Attribute To Index** | Atributo continuo → índice discreto |
| **Constraint Property** | Define compliance/damping/break para Constraints |
| **Constraints** | Genera primitivas de constraint para Soft Body |
| **Delete** | Elimina instancias por condición/falloff/grupo |
| **Extract Attributes** | Extrae atributos a POP separado |
| **Geo** ⭐ | Renderiza POPX Geometry con materiales por índice. Como Geometry COMP pero para POPX |
| **Light** | Parámetros de luz por instancia (Path Tracer) |
| **Material** | Disney PBR para Path Tracer. Base Color/Metallic/Roughness/IOR/Transmission |
| **Measure** | Calcula métricas (distancias, áreas) como atributos |
| **Merge** | Une múltiples POPX/POP geometrías |
| **Orient Curve** | Orienta instancias a lo largo de curva (Frenet/custom up) |
| **Orient Mesh** | Orienta instancias siguiendo normal del mesh |
| **Path Tracer** ⭐ | Ray tracing GPU. Disney BRDF. **Solo Windows**. Requiere Unpack previo para instancias |
| **Popxto** | POPX Geometry → formatos estándar |
| **Reorient** | Reorienta ejes locales sin mover instancias. Usar después de Convert |
| **Sbpp** | Soft Body Post Process: smooth + stretch stress color |
| **Ssfr** | Screen Space Falloff Remap: intensidad según posición en pantalla |
| **Unpack** | Descomprime POPX packed → geometría realizada |
| **Visualize Frame** | Debug: muestra ejes locales de cada instancia |
| **Voxelize** | Mesh → textura 3D + Grid POP de voxels |

---

## SIMULATIONS (9) — independientes, con Initialize/Start/Play/Step

| Op | Para qué |
|---|---|
| **DLA** | Diffusion-Limited Aggregation. Patrones coral/cristal. 3 outputs: Points/Lines/Walkers |
| **DLG** | Differential Line Growth. Necesita line strips como input |
| **Flow** ⭐ | Navier-Stokes GPU. Humo/fuego. Modos Simple (Particle POP externo) y Advect (propio) |
| **Mesh Fill** | Trails orgánicos que llenan el interior de un mesh |
| **Particle** ⭐ | SPH/PBF/Grains. Se combina con Particle POP nativo (emisión) + POPX Particle (física) |
| **Physarum** ⭐ | Slime mold. 2D o 3D. 3 outputs: Particles/Trail TOP/Deposit TOP |
| **SA** | Strange Attractors. Lorenz, Thomas, Aizawa, custom equations |
| **Shortest Path** | Caminos mínimos entre puntos en red de geometría |
| **Soft Body** ⭐ | XPBD sobre mesh deformable. Necesita Constraints en input 1 |

> Para detalle de Flow, Soft Body, Particle y Physarum → **td_popx_simulations.md**
